"""Pipeline de scan en streaming SSE : étapes et format des événements."""

import asyncio
import time
from collections.abc import AsyncGenerator

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.services.cookies import check_cookies_from_response
from app.services.security_headers import check_security_headers_from_response
from app.services.tls import run_tls_checks
from app.utils.http_fetch import fetch_https
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_validator import URLValidationError, validate_and_normalize_url


async def _emit_step_and_run(step_name: str, msg_check: str, msg_done: str, check_fn, *args, **kwargs) -> tuple[list[str], object]:
    """Émet step_check, exécute la vérification, émet step_done. Retourne (chunks, result).

    Args:
        step_name: Nom de l'étape (ex. "tls", "headers").
        msg_check: Message pour l'événement step_check.
        msg_done: Message pour l'événement step_done.
        check_fn: Fonction sync ou async à appeler.
        *args, **kwargs: Arguments passés à check_fn.

    Returns:
        tuple[list[str], object]: (messages SSE à yield, résultat de check_fn).
    """
    chunks = [sse_message("step", {"step": f"{step_name}_check", "message": msg_check})]
    if asyncio.iscoroutinefunction(check_fn):
        result = await check_fn(*args, **kwargs)
    else:
        result = check_fn(*args, **kwargs)
    chunks.append(sse_message("step", {"step": f"{step_name}_done", "message": msg_done}))
    return chunks, result


def _timeout_error_message() -> str:
    """Message SSE d'erreur pour dépassement du délai global."""
    return sse_message("error", {"message": "Délai global du scan dépassé.", "status_code": 408})


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
    https_response = await fetch_https(normalized_url)

    chunks, tls_result = await _emit_step_and_run(
        "tls",
        "Vérification TLS/HTTPS…",
        "TLS/HTTPS vérifié.",
        run_tls_checks,
        normalized_url,
        https_response=https_response,
    )
    for c in chunks:
        yield c

    if _over_global():
        yield _timeout_error_message()
        return
    chunks, headers_result = await _emit_step_and_run(
        "headers",
        "Vérification Security Headers…",
        "Security Headers vérifiés.",
        check_security_headers_from_response,
        https_response,
    )
    for c in chunks:
        yield c

    if _over_global():
        yield _timeout_error_message()
        return
    chunks, cookies_result = await _emit_step_and_run(
        "cookies",
        "Vérification Cookies…",
        "Cookies vérifiés.",
        check_cookies_from_response,
        https_response,
        is_https=tls_result.https_enabled,
    )
    for c in chunks:
        yield c

    valid = tls_result.is_posture_valid()
    yield sse_message(
        "result",
        {
            "valid": valid,
            "url": normalized_url,
            "tls": tls_result.to_dict(),
            "headers": headers_result.to_dict(),
            "cookies": cookies_result.to_dict(),
        },
    )


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
