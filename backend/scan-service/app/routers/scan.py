"""Route de scan (posture sécurité) — pipeline en streaming SSE."""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config_loader import get_ssrf_settings
from app.schemas.scan import ScanRequest
from app.services.scan_runner import run_scan
from app.utils.ssrf import check_ssrf
from app.utils.url_validator import URLValidationError, validate_and_normalize_url

router = APIRouter(prefix="/api", tags=["scan"])


def _sse_message(event: str, data: dict) -> str:
    """Formate un message Server-Sent Events."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _scan_stream_generator(url: str):
    """Générateur SSE : émet un événement à chaque étape de la pipeline."""
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

        yield _sse_message("result", {"valid": True, "url": normalized_url})
    except URLValidationError as e:
        yield _sse_message("error", {"message": str(e), "status_code": 400})


@router.post(
    "/scan",
    summary="Lancer un scan",
    description="Pipeline en streaming : renvoie les étapes au fur et à mesure (SSE).",
)
async def post_scan(body: ScanRequest) -> StreamingResponse:
    """Scan en streaming : un événement SSE à chaque étape (validation, SSRF, scan).

    Événements : step (validation_url, url_validated, ssrf_check, ssrf_ok, scan_run, scan_done),
    puis result ou error.
    """
    return StreamingResponse(
        _scan_stream_generator(body.url),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
