"""Route de scan (posture sécurité) — pipeline en streaming SSE et export PDF."""

import logging
import os
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.schemas.scan import ScanRequest
from app.services.scan_runner import ScanRunError, run_scan_to_result
from app.services.scan_stream import scan_stream_generator
from app.utils.url_validator import URLValidationError

# Clé API pour les appels service-to-service (endpoint interne).
# Si définie, le header X-Internal-Api-Key doit correspondre.
INTERNAL_API_KEY = os.getenv("SCAN_SERVICE_INTERNAL_API_KEY")

_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie la clé API interne si SCAN_SERVICE_INTERNAL_API_KEY est définie.

    En dev (variable non définie), l'accès est autorisé sans clé.
    """
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY_INTERNAL_API_KEY = Depends(_verify_internal_api_key)


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
PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://localhost:8013")
PDF_SERVICE_INTERNAL_API_KEY = os.getenv("PDF_SERVICE_INTERNAL_API_KEY")
FETCH_SCAN_TIMEOUT = 10.0
PDF_REQUEST_TIMEOUT = 60.0


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

    pdf_endpoint = urljoin(f"{PDF_SERVICE_URL.rstrip('/')}/", "api/report/pdf")
    payload = {
        "url": scan_data.url,
        "score": scan_data.score,
        "timestamp": scan_data.timestamp,
        "duration": scan_data.duration,
        "findings": scan_data.findings,
    }
    params = {"lang": lang if lang in ("fr", "en") else "fr", "include_matrices": include_matrices}
    pdf_headers = {}
    if PDF_SERVICE_INTERNAL_API_KEY:
        pdf_headers["X-Internal-Api-Key"] = PDF_SERVICE_INTERNAL_API_KEY

    async with httpx.AsyncClient(timeout=PDF_REQUEST_TIMEOUT) as client:
        pdf_resp = await client.post(pdf_endpoint, json=payload, params=params, headers=pdf_headers)
        if pdf_resp.status_code >= 400:
            logger.warning("Erreur pdf-service pour export PDF: %s %s", pdf_resp.status_code, pdf_resp.text[:200])
            return Response(status_code=502, content="Impossible de générer le PDF")

    pdf_bytes = pdf_resp.content
    host = scan_data.url.replace("https://", "").replace("http://", "").split("/")[0][:30]
    filename = f"scan-{host}-{scan_data.timestamp[:10]}.pdf".replace(":", "-")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


class InternalScanRequest(BaseModel):
    """Requête pour l'endpoint interne (scheduler)."""

    url: str = Field(..., description="URL à scanner")


@router.post(
    "/internal/scan/run",
    summary="[Interne] Exécuter un scan et retourner le résultat en JSON",
    description="Utilisé par le scheduler user-service. Si SCAN_SERVICE_INTERNAL_API_KEY est définie, " "le header X-Internal-Api-Key est requis.",
)
async def internal_run_scan(
    body: InternalScanRequest,
    _: None = _VERIFY_INTERNAL_API_KEY,
) -> dict:
    """Exécute le scan et retourne le résultat en JSON (pas de SSE)."""
    try:
        return await run_scan_to_result(body.url)
    except URLValidationError as e:
        return {"status": "error", "message": str(e), "status_code": 400}
    except ScanRunError as e:
        return {"status": "error", "message": e.message, "status_code": e.status_code}
    except Exception as e:
        logger.exception("Erreur inattendue lors du scan interne: %s", e)
        return {"status": "error", "message": str(e), "status_code": 500}


@router.post(
    "/scan",
    summary="Lancer un scan",
    description="Pipeline en streaming : renvoie les étapes au fur et à mesure (SSE).",
)
async def post_scan(body: ScanRequest, request: Request) -> StreamingResponse:
    """Scan en streaming : un événement SSE à chaque étape (validation, SSRF, scan).

    Événements : step (validation_url_check/done, ssrf_check/done, fetch_https_check/done, tls_check/done, …),
    puis result ou error. Si Authorization présent et scan réussi, sauvegarde dans l'historique.
    """
    authorization = request.headers.get("Authorization")
    return StreamingResponse(
        scan_stream_generator(body.url, authorization=authorization),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
