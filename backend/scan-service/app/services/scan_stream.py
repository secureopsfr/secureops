"""Pipeline de scan en streaming SSE : étapes et format des événements."""

import json
import time
from collections.abc import AsyncGenerator

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.services.scan_runner import run_tls_checks
from app.utils.ssrf import check_ssrf
from app.utils.url_validator import URLValidationError, validate_and_normalize_url


def _sse_message(event: str, data: dict) -> str:
    """Formate un message Server-Sent Events.

    Args:
        event: Nom de l'événement SSE.
        data: Données JSON à envoyer.

    Returns:
        str: Bloc SSE (event + data + double newline).
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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
        start = time.monotonic()
        scan_global = get_scan_timeouts().scan_global

        def _over_global() -> bool:
            return (time.monotonic() - start) > scan_global

        yield _sse_message("step", {"step": "validation_url", "message": "Validation de l'URL…"})
        normalized_url = validate_and_normalize_url(url)
        yield _sse_message("step", {"step": "url_validated", "message": "URL validée et normalisée."})

        if _over_global():
            yield _sse_message("error", {"message": "Délai global du scan dépassé.", "status_code": 408})
            return
        yield _sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (résolution DNS)…"})
        await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
        yield _sse_message("step", {"step": "ssrf_ok", "message": "Vérification SSRF OK."})

        if _over_global():
            yield _sse_message("error", {"message": "Délai global du scan dépassé.", "status_code": 408})
            return
        yield _sse_message("step", {"step": "tls_check", "message": "Vérification TLS/HTTPS…"})
        tls_result = await run_tls_checks(normalized_url)
        yield _sse_message("step", {"step": "tls_done", "message": "TLS/HTTPS vérifié."})

        valid = (
            tls_result.https_enabled
            and (tls_result.http_redirects_to_https is None or tls_result.http_redirects_to_https)  # noqa: W503
            and (tls_result.certificate_status is None or tls_result.certificate_status == "valid")  # noqa: W503
        )
        yield _sse_message(
            "result",
            {
                "valid": valid,
                "url": normalized_url,
                "tls": {
                    "https_enabled": tls_result.https_enabled,
                    "http_redirects_to_https": tls_result.http_redirects_to_https,
                    "certificate_status": tls_result.certificate_status,
                    "findings": list(tls_result.findings),
                },
            },
        )
    except URLValidationError as e:
        yield _sse_message("error", {"message": str(e), "status_code": 400})
