"""Pipeline de scan en streaming SSE : étapes et format des événements.

Exceptions :
  - Remontées vers l'appelant (émises en événement error) : URLValidationError (400).
  - Gérées en interne (événement error) : dépassement du délai global (408), site inaccessible
    / timeout / erreur TLS sur le fetch HTTPS principal (503/504/502).
  - Path checks (exposed_files, directory_listing, robots.txt) : retournent fetch_ok=False
    si requête échouée ; aucune exception levée.
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from common.logging_config import correlation_id_ctx

from app.catalogue.category_summaries import build_category_summaries
from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.errors.fetch_errors import (
    build_sse_error_payload,
    build_timeout_global_error_payload,
    build_unexpected_error_payload,
    build_validation_error_payload,
)
from app.models.scan_result import ScanResult
from app.services.cookies import check_cookies_from_response
from app.services.directory_listing import run_directory_listing_checks
from app.services.exposed_files import run_exposed_files_checks
from app.services.normalization import normalize_results
from app.services.robots_txt import run_robots_txt_checks
from app.services.scoring import compute_score
from app.services.security_headers import check_security_headers_from_response
from app.services.tech_fingerprinting import check_tech_fingerprinting_from_response
from app.services.tls import run_tls_checks
from app.utils.http_fetch import get_with_client_or_error, scan_client
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import build_https_url
from app.utils.url_validator import URLValidationError, validate_and_normalize_url

logger = logging.getLogger(__name__)


def _log_scan_complete(
    duration_seconds: float,
    nb_findings: int,
    status: str,
) -> None:
    """Log structuré à la fin du scan (roadmap §6).

    Args:
        duration_seconds: Durée du scan en secondes.
        nb_findings: Nombre de findings (0 en cas d'erreur).
        status: Statut final (success, error_400, error_408, error_500, error_502, error_503, error_504).
    """
    request_id = correlation_id_ctx.get() or "unknown"
    logger.info(
        "Scan terminé",
        extra={
            "request_id": request_id,
            "duration_seconds": round(duration_seconds, 3),
            "nb_findings": nb_findings,
            "status": status,
        },
    )


@dataclass
class ScanContext:
    """Contexte partagé entre les étapes de la pipeline.

    Attributes:
        normalized_url: URL normalisée scannée.
        https_url: URL HTTPS de base (pour path checks).
        client: Client httpx partagé.
        https_response: Réponse de la requête HTTPS initiale.
        results: Résultats des étapes (rempli au fur et à mesure).
    """

    normalized_url: str
    https_url: str
    client: object
    https_response: object
    results: dict[str, object] = field(default_factory=dict)


async def _emit_step_and_run(step_name: str, msg_check: str, msg_done: str, step_fn: Callable, ctx: ScanContext) -> tuple[list[str], object]:
    """Émet step_check, exécute la vérification, émet step_done. Retourne (chunks, result).

    Args:
        step_name: Nom de l'étape (ex. "tls", "headers").
        msg_check: Message pour l'événement step_check.
        msg_done: Message pour l'événement step_done.
        step_fn: Fonction sync ou async à appeler avec ctx.
        ctx: Contexte de scan.

    Returns:
        tuple[list[str], object]: (messages SSE à yield, résultat de step_fn).
    """
    chunks = [sse_message("step", {"step": f"{step_name}_check", "message": msg_check})]
    result = step_fn(ctx)
    if asyncio.iscoroutine(result):
        result = await result
    chunks.append(sse_message("step", {"step": f"{step_name}_done", "message": msg_done}))
    return chunks, result


def _timeout_error_message() -> str:
    """Message SSE d'erreur pour dépassement du délai global."""
    return sse_message("error", build_timeout_global_error_payload())


def _build_result_payload(
    url: str,
    results: dict[str, object],
    start_time: float,
) -> dict:
    """Construit le payload normalisé (ScanResult) pour l'événement SSE result.

    Args:
        url: URL normalisée scannée.
        results: Dict clé → résultat (tls, headers, cookies, exposed_files, directory_listing, robots_txt, tech_fingerprinting).
        start_time: Timestamp monotonic du début du scan.

    Returns:
        dict: Payload sérialisable pour {event: result, data: {...}}.
    """
    findings = normalize_results(results)
    findings_tuple = tuple(findings)
    score = compute_score(findings_tuple)
    duration = time.monotonic() - start_time
    timestamp = datetime.now(timezone.utc).isoformat()
    scan_result = ScanResult(
        url=url,
        timestamp=timestamp,
        duration=duration,
        score=score,
        findings=findings_tuple,
    )
    payload = scan_result.to_dict()
    payload["category_summaries"] = build_category_summaries(findings_tuple)
    return payload


# Étapes de la pipeline : (step_name, msg_check, msg_done, step_fn)
_SCAN_STEPS: list[tuple[str, str, str, Callable]] = [
    (
        "tls",
        "Vérification TLS/HTTPS…",
        "TLS/HTTPS vérifié.",
        lambda ctx: run_tls_checks(
            ctx.normalized_url,
            https_response=ctx.https_response,
            client=ctx.client,
        ),
    ),
    (
        "headers",
        "Vérification Security Headers…",
        "Security Headers vérifiés.",
        lambda ctx: check_security_headers_from_response(ctx.https_response),
    ),
    (
        "cookies",
        "Vérification Cookies…",
        "Cookies vérifiés.",
        lambda ctx: check_cookies_from_response(
            ctx.https_response,
            is_https=ctx.results["tls"].https_enabled,
        ),
    ),
    (
        "exposed_files",
        "Vérification fichiers sensibles exposés…",
        "Fichiers sensibles vérifiés.",
        lambda ctx: run_exposed_files_checks(ctx.https_url, client=ctx.client),
    ),
    (
        "directory_listing",
        "Vérification directory listing…",
        "Directory listing vérifié.",
        lambda ctx: run_directory_listing_checks(ctx.https_url, client=ctx.client),
    ),
    (
        "robots_txt",
        "Vérification robots.txt…",
        "robots.txt vérifié.",
        lambda ctx: run_robots_txt_checks(ctx.https_url, client=ctx.client),
    ),
    (
        "tech_fingerprinting",
        "Fingerprinting technologique…",
        "Tech fingerprinting vérifié.",
        lambda ctx: check_tech_fingerprinting_from_response(ctx.https_response),
    ),
]


async def _run_checks_with_client(
    normalized_url: str,
    client: object,
    over_global: Callable[[], bool],
    start_time: float,
    authorization: str | None = None,
) -> AsyncGenerator[str, None]:
    """Exécute les étapes de vérification avec le client partagé."""
    https_url = build_https_url(normalized_url)
    fetch_result = await get_with_client_or_error(client, https_url, follow_redirects=True)

    # Détection précoce : site inaccessible, timeout ou erreur TLS → événement error
    if not fetch_result.success:
        duration = time.monotonic() - start_time
        _log_scan_complete(duration, 0, f"error_{fetch_result.status_code}")
        yield sse_message("error", build_sse_error_payload(fetch_result))
        return

    yield sse_message("step", {"step": "fetch_https_done", "message": "Page HTTPS récupérée."})

    https_response = fetch_result.response
    ctx = ScanContext(
        normalized_url=normalized_url,
        https_url=https_url,
        client=client,
        https_response=https_response,
    )

    for step_name, msg_check, msg_done, step_fn in _SCAN_STEPS:
        chunks, result = await _emit_step_and_run(step_name, msg_check, msg_done, step_fn, ctx)
        ctx.results[step_name] = result
        for c in chunks:
            yield c
        if over_global():
            duration = time.monotonic() - start_time
            _log_scan_complete(duration, 0, "error_408")
            yield _timeout_error_message()
            return

    payload = _build_result_payload(normalized_url, ctx.results, start_time)
    nb_findings = len(payload["findings"])
    duration = payload["duration"]
    _log_scan_complete(duration, nb_findings, "success")
    yield sse_message("result", payload)

    # Sauvegarde dans l'historique si utilisateur connecté (roadmap 0.2.0 §2)
    if authorization:
        try:
            from app.services.scan_history_save import save_scan_to_history

            scan_id = await save_scan_to_history(payload, authorization)
            if scan_id:
                yield sse_message("save_done", {"scan_id": scan_id})
        except Exception as e:
            logger.warning("Sauvegarde historique échouée: %s", e)
            yield sse_message("save_failed", {"message": str(e)})


async def _run_pipeline_steps(url: str, authorization: str | None = None) -> AsyncGenerator[str, None]:
    """Exécute les étapes de la pipeline (validation, SSRF, fetch, checks)."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    yield sse_message("step", {"step": "validation_url_check", "message": "Validation de l'URL…"})
    normalized_url = validate_and_normalize_url(url)
    yield sse_message("step", {"step": "validation_url_done", "message": "URL validée et normalisée."})

    if _over_global():
        _log_scan_complete(time.monotonic() - start, 0, "error_408")
        yield _timeout_error_message()
        return
    yield sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (résolution DNS)…"})
    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    yield sse_message("step", {"step": "ssrf_done", "message": "Vérification SSRF OK."})

    if _over_global():
        _log_scan_complete(time.monotonic() - start, 0, "error_408")
        yield _timeout_error_message()
        return
    yield sse_message("step", {"step": "fetch_https_check", "message": "Récupération de la page HTTPS…"})

    async with scan_client() as client:
        async for chunk in _run_checks_with_client(normalized_url, client, _over_global, start, authorization=authorization):
            yield chunk


async def scan_stream_generator(url: str, authorization: str | None = None) -> AsyncGenerator[str, None]:
    """Générateur SSE : émet un événement à chaque étape de la pipeline.

    Le timeout global (scan_global) est vérifié avant chaque étape longue ; si dépassé, un
    événement error est envoyé et le stream s'arrête.

    Args:
        url: URL à scanner (sera validée puis vérifiée SSRF).

    Yields:
        str: Blocs SSE (event + data).

    Raises:
        Aucune. Les erreurs sont émises en événements SSE (error 400 pour URLValidationError,
        error 408 pour timeout global, error 500 pour exception inattendue). Les erreurs réseau
        dans les steps sont gérées en interne (résultats avec fetch_ok=False).
    """
    start = time.monotonic()
    try:
        async for chunk in _run_pipeline_steps(url, authorization=authorization):
            yield chunk
    except URLValidationError as e:
        _log_scan_complete(time.monotonic() - start, 0, "error_400")
        yield sse_message("error", build_validation_error_payload(str(e)))
    except Exception as e:
        _log_scan_complete(time.monotonic() - start, 0, "error_500")
        yield sse_message("error", build_unexpected_error_payload(str(e)))
