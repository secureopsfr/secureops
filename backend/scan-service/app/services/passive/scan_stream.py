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

from common.logging_config import correlation_id_ctx

from app.config_loader import get_scan_timeouts
from app.errors.fetch_errors import (
    build_sse_error_payload,
    build_timeout_global_error_payload,
    build_unexpected_error_payload,
    build_validation_error_payload,
)
from app.services.passive._scan_core import SCAN_STEPS, ScanContext, build_result_payload
from app.services.scan_preflight_common import emit_events, has_error_event, run_single_preflight
from app.services.scan_stream_common import emit_save_events
from app.utils.http_fetch import get_with_client_or_error, http_request_category, log_http_metrics, scan_client
from app.utils.sse import sse_message
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import URLValidationError

logger = logging.getLogger(__name__)


def _extract_anomaly_count(result: object) -> int:
    """Retourne le nombre d'anomalies detectees pour un resultat d'etape."""
    findings = result.get("findings") if isinstance(result, dict) else getattr(result, "findings", None)
    if findings is None:
        findings = getattr(result, "issues", None)
    if isinstance(findings, (list, tuple, set)):
        return len(findings)
    return 0


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


async def _run_step(step_name: str, step_fn: Callable, ctx: ScanContext) -> AsyncGenerator[str, None]:
    """Générateur : yield step_check AVANT l'exécution, puis step_done après.

    Permet au frontend (via polling) de voir l'état loading (_check en DB)
    pendant que le step s'exécute, avant que _done ne soit stocké.

    Args:
        step_name: Nom de l'étape (ex. "tls", "headers").
        step_fn: Fonction sync ou async à appeler avec ctx.
        ctx: Contexte de scan (ctx.results[step_name] est peuplé après l'exécution).
    """
    yield sse_message("step", {"step": f"{step_name}_check", "message": ""})
    result = step_fn(ctx)
    if asyncio.iscoroutine(result):
        result = await result
    ctx.results[step_name] = result
    anomaly_count = _extract_anomaly_count(result)
    yield sse_message(
        "step",
        {
            "step": f"{step_name}_done",
            "message": "",
            "anomaly_count": anomaly_count,
        },
    )


def _timeout_error_message() -> str:
    """Message SSE d'erreur pour dépassement du délai global."""
    return sse_message("error", build_timeout_global_error_payload())


# Étapes SSE: (step_name, step_fn)
_SCAN_STEP_FN_MAP = dict(SCAN_STEPS)
# Étapes réservées au frontend (robots.txt, sitemap, intégrité HTML) — ignorées si scan_type == "backend"
_FRONTEND_ONLY_STEPS: frozenset[str] = frozenset({"robots_txt", "sitemap", "integrity"})
_SCAN_SSE_STEPS: list[tuple[str, Callable]] = [
    ("tls", _SCAN_STEP_FN_MAP["tls"]),
    ("headers", _SCAN_STEP_FN_MAP["headers"]),
    ("cache", _SCAN_STEP_FN_MAP["cache"]),
    ("cookies", _SCAN_STEP_FN_MAP["cookies"]),
    ("exposed_files", _SCAN_STEP_FN_MAP["exposed_files"]),
    ("directory_listing", _SCAN_STEP_FN_MAP["directory_listing"]),
    ("robots_txt", _SCAN_STEP_FN_MAP["robots_txt"]),
    ("sitemap", _SCAN_STEP_FN_MAP["sitemap"]),
    ("tech_fingerprinting", _SCAN_STEP_FN_MAP["tech_fingerprinting"]),
    ("information_disclosure", _SCAN_STEP_FN_MAP["information_disclosure"]),
    ("integrity", _SCAN_STEP_FN_MAP["integrity"]),
    ("cors_cross_origin", _SCAN_STEP_FN_MAP["cors_cross_origin"]),
    ("methodes_http_et_redirections", _SCAN_STEP_FN_MAP["methodes_http_et_redirections"]),
    ("api_checks", _SCAN_STEP_FN_MAP["api_checks"]),
    ("formats", _SCAN_STEP_FN_MAP["formats"]),
    ("api_page", _SCAN_STEP_FN_MAP["api_page"]),
]


async def _run_checks_with_client(
    normalized_url: str,
    client: object,
    over_global: Callable[[], bool],
    start_time: float,
    authorization: str | None = None,
    scan_type: str = "frontend",
) -> AsyncGenerator[str, None]:
    """Exécute les étapes de vérification avec le client partagé."""
    https_url = get_scan_base_url(normalized_url)
    try:
        with http_request_category("initial_fetch"):
            fetch_result = await get_with_client_or_error(client, https_url, follow_redirects=True)

        # Détection précoce : site inaccessible, timeout ou erreur TLS -> événement error
        if not fetch_result.success:
            duration = time.monotonic() - start_time
            _log_scan_complete(duration, 0, f"error_{fetch_result.status_code}")
            yield sse_message("error", build_sse_error_payload(fetch_result))
            return

        yield sse_message("step", {"step": "fetch_https_done", "message": ""})

        https_response = fetch_result.response
        ctx = ScanContext(
            normalized_url=normalized_url,
            https_url=https_url,
            client=client,
            https_response=https_response,
            scan_type=scan_type,
        )

        for step_name, step_fn in _SCAN_SSE_STEPS:
            if scan_type == "backend" and step_name in _FRONTEND_ONLY_STEPS:
                continue
            with http_request_category(step_name):
                async for chunk in _run_step(step_name, step_fn, ctx):
                    yield chunk
            if over_global():
                duration = time.monotonic() - start_time
                _log_scan_complete(duration, 0, "error_408")
                yield _timeout_error_message()
                return

        payload = build_result_payload(normalized_url, ctx.results, start_time, scan_type=scan_type)
        nb_findings = len(payload["findings"])
        duration = payload["duration"]
        _log_scan_complete(duration, nb_findings, "success")
        yield sse_message("result", payload)

        # Sauvegarde dans l'historique si utilisateur connecté (roadmap 0.2.0 §2)
        async for chunk in emit_save_events(
            payload=payload,
            authorization=authorization,
            logger=logger,
            mode_label="Passive",
        ):
            yield chunk
    finally:
        log_http_metrics(client, "scan-stream", url=https_url)


async def _run_pipeline_steps(
    url: str,
    authorization: str | None = None,
    scan_type: str = "frontend",
) -> AsyncGenerator[str, None]:
    """Exécute les étapes de la pipeline (validation, SSRF, fetch, checks)."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    normalized_url, preflight_events = await run_single_preflight(
        url=url,
        over_global=_over_global,
        timeout_error_message_factory=_timeout_error_message,
    )
    async for chunk in emit_events(preflight_events):
        yield chunk
    if has_error_event(preflight_events):
        _log_scan_complete(time.monotonic() - start, 0, "error_408")
        return
    if normalized_url is None:
        return

    async with scan_client() as client:
        async for chunk in _run_checks_with_client(
            normalized_url,
            client,
            _over_global,
            start,
            authorization=authorization,
            scan_type=scan_type,
        ):
            yield chunk


async def scan_stream_generator(
    url: str,
    authorization: str | None = None,
    *,
    scan_type: str = "frontend",
) -> AsyncGenerator[str, None]:
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
        async for chunk in _run_pipeline_steps(url, authorization=authorization, scan_type=scan_type):
            yield chunk
    except URLValidationError as e:
        _log_scan_complete(time.monotonic() - start, 0, "error_400")
        yield sse_message("error", build_validation_error_payload(str(e)))
    except Exception as e:
        _log_scan_complete(time.monotonic() - start, 0, "error_500")
        yield sse_message("error", build_unexpected_error_payload(str(e)))
