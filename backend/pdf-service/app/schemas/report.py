"""Schémas Pydantic pour les routes du pdf-service."""

from pydantic import BaseModel, Field

from app.schemas.finding import Finding


class ReportPdfBody(BaseModel):
    """Payload attendu pour la génération PDF (résultat de scan)."""

    url: str = Field(..., description="URL scannée")
    score: int | None = Field(None, description="Score /100")
    timestamp: str = Field("", description="Horodatage ISO du scan")
    duration: float = Field(0.0, description="Durée du scan en secondes")
    findings: list[Finding] = Field(default_factory=list, description="Liste des findings")
