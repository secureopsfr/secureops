"""Route de génération de rapports PDF."""

import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response

from app.schemas.report import ReportPdfBody
from app.services.pdf_report import generate_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["report"])

PDF_SERVICE_INTERNAL_API_KEY = os.getenv("PDF_SERVICE_INTERNAL_API_KEY")
_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie la clé API interne si PDF_SERVICE_INTERNAL_API_KEY est définie.

    En dev (variable non définie), l'accès est autorisé sans clé.
    Le gateway et le scan-service envoient cette clé lors des appels.
    """
    if not PDF_SERVICE_INTERNAL_API_KEY:
        return
    if x_internal_api_key != PDF_SERVICE_INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY_INTERNAL_API_KEY = Depends(_verify_internal_api_key)


@router.post(
    "/report/pdf",
    summary="Générer un rapport PDF",
    description="Génère un rapport PDF à partir du payload de scan (url, score, timestamp, duration, findings). "
    "Si PDF_SERVICE_INTERNAL_API_KEY est définie, le header X-Internal-Api-Key est requis.",
    response_class=Response,
)
def report_pdf(
    body: ReportPdfBody,
    _: None = _VERIFY_INTERNAL_API_KEY,
    lang: str = "fr",
    include_matrices: bool = True,
) -> Response:
    """Génère le PDF et le retourne en binaire."""
    lang = lang if lang in ("fr", "en") else "fr"
    pdf_bytes = generate_pdf(
        url=body.url,
        score=body.score,
        timestamp=body.timestamp,
        duration=body.duration,
        findings=body.findings,
        result_mode=body.result_mode,
        page_results=body.page_results,
        include_matrices=include_matrices,
        lang=lang,
    )
    host = body.url.replace("https://", "").replace("http://", "").split("/")[0][:30]
    filename = f"scan-{host}-{body.timestamp[:10]}.pdf".replace(":", "-")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
