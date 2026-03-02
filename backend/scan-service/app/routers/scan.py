"""Route de scan (posture sécurité) — pipeline en streaming SSE."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.scan import ScanRequest
from app.services.scan_stream import scan_stream_generator

router = APIRouter(prefix="/api", tags=["scan"])


@router.post(
    "/scan",
    summary="Lancer un scan",
    description="Pipeline en streaming : renvoie les étapes au fur et à mesure (SSE).",
)
async def post_scan(body: ScanRequest, request: Request) -> StreamingResponse:
    """Scan en streaming : un événement SSE à chaque étape (validation, SSRF, scan).

    Événements : step (validation_url, url_validated, ssrf_check, ssrf_ok, scan_run, scan_done),
    puis result ou error. Si Authorization présent et scan réussi, sauvegarde dans l'historique.
    """
    authorization = request.headers.get("Authorization")
    return StreamingResponse(
        scan_stream_generator(body.url, authorization=authorization),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
