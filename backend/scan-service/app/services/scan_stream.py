"""Pipeline de scan en streaming SSE : étapes et format des événements."""

import asyncio
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.models.check_results import CheckResultProtocol
from app.services.cookies import check_cookies_from_response
from app.services.directory_listing import run_directory_listing_checks
from app.services.exposed_files import run_exposed_files_checks
from app.services.security_headers import check_security_headers_from_response
from app.services.tls import run_tls_checks
from app.utils.http_fetch import get_with_client, scan_client
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import build_https_url
from app.utils.url_validator import URLValidationError, validate_and_normalize_url


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
    return sse_message("error", {"message": "Délai global du scan dépassé.", "status_code": 408})


def _build_result_payload(
    valid: bool,
    url: str,
    results: dict[str, CheckResultProtocol],
) -> dict:
    """Construit le payload de l'événement SSE result à partir des résultats.

    Args:
        valid: Posture TLS valide (is_posture_valid).
        url: URL normalisée scannée.
        results: Dict clé → résultat (tls, headers, cookies, exposed_files, directory_listing).

    Returns:
        dict: Payload sérialisable pour {event: result, data: {...}}.
    """
    payload: dict = {"valid": valid, "url": url}
    for key, result in results.items():
        payload[key] = result.to_dict()
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
]


async def _run_checks_with_client(
    normalized_url: str,
    client: object,
    over_global: Callable[[], bool],
) -> AsyncGenerator[str, None]:
    """Exécute les étapes de vérification avec le client partagé."""
    https_url = build_https_url(normalized_url)
    https_response = await get_with_client(client, https_url, follow_redirects=True)
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
            yield _timeout_error_message()
            return

    tls_result = ctx.results["tls"]
    payload = _build_result_payload(tls_result.is_posture_valid(), normalized_url, ctx.results)
    yield sse_message("result", payload)


async def _run_pipeline_steps(url: str) -> AsyncGenerator[str, None]:
    """Exécute les étapes de la pipeline (validation, SSRF, fetch, checks)."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    yield sse_message("step", {"step": "validation_url", "message": "Validation de l'URL…"})
    normalized_url = validate_and_normalize_url(url)
    yield sse_message("step", {"step": "url_validated", "message": "URL validée et normalisée."})

    if _over_global():
        yield _timeout_error_message()
        return
    yield sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (résolution DNS)…"})
    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    yield sse_message("step", {"step": "ssrf_ok", "message": "Vérification SSRF OK."})

    if _over_global():
        yield _timeout_error_message()
        return
    yield sse_message("step", {"step": "fetch_https", "message": "Récupération de la page HTTPS…"})

    async with scan_client() as client:
        async for chunk in _run_checks_with_client(normalized_url, client, _over_global):
            yield chunk


async def scan_stream_generator(url: str) -> AsyncGenerator[str, None]:
    """Générateur SSE : émet un événement à chaque étape de la pipeline.

    Le timeout global (scan_global) est vérifié avant chaque étape longue ; si dépassé, un
    événement error est envoyé et le stream s'arrête.

    Args:
        url: URL à scanner (sera validée puis vérifiée SSRF).

    Yields:
        str: Blocs SSE (event + data).
    """
    try:
        async for chunk in _run_pipeline_steps(url):
            yield chunk
    except URLValidationError as e:
        yield sse_message("error", {"message": str(e), "status_code": 400})
    except Exception as e:
        yield sse_message(
            "error",
            {"message": f"Erreur inattendue lors du scan : {e!s}", "status_code": 500},
        )
