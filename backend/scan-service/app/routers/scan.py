"""Route de scan (posture sécurité) — pipeline en streaming SSE et export PDF."""

import logging
import os
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.schemas.scan import ScanRequest
from app.services.pdf_report import generate_pdf
from app.services.scan_stream import scan_stream_generator


class ScanForPdfSchema(BaseModel):
    """Schéma attendu pour la génération PDF (réponse user-service)."""

    url: str
    score: int | None = None
    timestamp: str = ""
    duration: float = 0.0
    findings: list[dict] = Field(default_factory=list)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scan"])

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
FETCH_SCAN_TIMEOUT = 10.0


@router.get(
    "/scan/export/pdf",
    summary="Exporter un scan en PDF",
    description="Génère un rapport PDF pour un scan sauvegardé. Auth requise.",
)
async def export_scan_pdf(
    request: Request,
    scan_id: str,
    include_matrices: bool = True,
    lang: str = "fr",
) -> Response:
    """Récupère le scan depuis user-service et génère le PDF."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return Response(status_code=401, content="Authentification requise")

    url = urljoin(f"{GATEWAY_URL.rstrip('/')}/", f"user/api/scans/history/{scan_id}")
    headers = {"Authorization": authorization}

    async with httpx.AsyncClient(timeout=FETCH_SCAN_TIMEOUT) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            return Response(status_code=404, content="Scan non trouvé")
        if resp.status_code == 401:
            return Response(status_code=401, content="Authentification requise")
        if resp.status_code >= 400:
            logger.warning("Erreur récupération scan pour PDF: %s %s", resp.status_code, resp.text[:200])
            return Response(status_code=502, content="Impossible de récupérer le scan")

    data = resp.json()
    try:
        scan_data = ScanForPdfSchema.model_validate(data)
    except Exception as e:
        logger.warning("Schéma scan invalide pour PDF: %s", e)
        return Response(status_code=502, content="Données du scan invalides")

    pdf_bytes = generate_pdf(
        url=scan_data.url,
        score=scan_data.score,
        timestamp=scan_data.timestamp,
        duration=scan_data.duration,
        findings=scan_data.findings,
        include_matrices=include_matrices,
        lang=lang if lang in ("fr", "en") else "fr",
    )

    host = scan_data.url.replace("https://", "").replace("http://", "").split("/")[0][:30]
    filename = f"scan-{host}-{scan_data.timestamp[:10]}.pdf".replace(":", "-")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


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
