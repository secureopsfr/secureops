"""Route de génération de rapports PDF."""

import logging

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.pdf_report import generate_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["report"])


class ReportPdfBody(BaseModel):
    """Payload attendu pour la génération PDF (résultat de scan)."""

    url: str = Field(..., description="URL scannée")
    score: int | None = Field(None, description="Score /100")
    timestamp: str = Field("", description="Horodatage ISO du scan")
    duration: float = Field(0.0, description="Durée du scan en secondes")
    findings: list[dict] = Field(default_factory=list, description="Liste des findings")


@router.post(
    "/report/pdf",
    summary="Générer un rapport PDF",
    description="Génère un rapport PDF à partir du payload de scan (url, score, timestamp, duration, findings).",
    response_class=Response,
)
def report_pdf(
    body: ReportPdfBody,
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
