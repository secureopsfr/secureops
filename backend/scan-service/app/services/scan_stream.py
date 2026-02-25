"""Pipeline de scan en streaming SSE : étapes et format des événements."""

import json
from collections.abc import AsyncGenerator

from app.config_loader import get_ssrf_settings
from app.services.scan_runner import run_scan, run_tls_checks
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

    Args:
        url: URL à scanner (sera validée puis vérifiée SSRF).

    Yields:
        str: Blocs SSE (event + data).
    """
    try:
        yield _sse_message("step", {"step": "validation_url", "message": "Validation de l'URL…"})
        normalized_url = validate_and_normalize_url(url)
        yield _sse_message("step", {"step": "url_validated", "message": "URL validée et normalisée."})

        yield _sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (résolution DNS)…"})
        await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
        yield _sse_message("step", {"step": "ssrf_ok", "message": "Vérification SSRF OK."})

        yield _sse_message("step", {"step": "scan_run", "message": "Exécution du scan…"})
        await run_scan(normalized_url)
        yield _sse_message("step", {"step": "scan_done", "message": "Scan terminé."})

        yield _sse_message("step", {"step": "tls_check", "message": "Vérification TLS/HTTPS…"})
        await run_tls_checks(normalized_url)
        yield _sse_message("step", {"step": "tls_done", "message": "TLS/HTTPS vérifié."})

        yield _sse_message("result", {"valid": True, "url": normalized_url})
    except URLValidationError as e:
        yield _sse_message("error", {"message": str(e), "status_code": 400})
