"""Schémas Pydantic pour les endpoints d'historique des scans."""

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

ScanType = Literal["frontend", "backend"]
ScanMode = Literal["passive", "intrusive", "destructive", "custom"]
ResultMode = Literal["single", "multi"]


class ScanCreateRequest(BaseModel):
    """Schéma pour la création d'un scan (appelé par scan-service)."""

    url: str = Field(..., description="URL scannée")
    scan_type: ScanType = Field(..., description="Type de scan : frontend ou backend")
    scan_mode: ScanMode = Field(default="passive", description="Mode de scan : passive, intrusive, destructive, custom")
    result_mode: ResultMode = Field(default="single", description="Mode du résultat : single ou multi")
    status: str = Field(default="success", description="Statut du scan")
    score: int | None = Field(None, description="Note /100")
    findings: List[dict[str, Any]] = Field(default_factory=list, description="Liste des findings")
    timestamp: str = Field(..., description="Horodatage ISO du scan")
    duration: float = Field(..., ge=0, description="Durée en secondes")
    category_summaries: Optional[List[dict[str, Any]]] = Field(
        default=None,
        description="Résumés par catégorie (checks_count, etc.)",
    )
    page_results: Optional[List[dict[str, Any]]] = Field(
        default=None,
        description="Résultats par page pour un scan multi-URL",
    )
    urls: Optional[List[str]] = Field(
        default=None,
        description="Liste des URLs scannées pour un scan multi-URL",
    )


class ScanListItem(BaseModel):
    """Élément de liste pour l'historique."""

    id: str = Field(..., description="UUID du scan")
    url: str = Field(..., description="URL scannée")
    scan_type: str = Field(..., description="Type de scan : frontend ou backend")
    scan_mode: str = Field(..., description="Mode de scan : passive, intrusive, destructive, custom")
    result_mode: ResultMode = Field(default="single", description="Mode du résultat : single ou multi")
    status: str = Field(..., description="Statut")
    score: int | None = Field(None, description="Note /100")
    timestamp: datetime = Field(..., description="Horodatage du scan")
    duration: float = Field(..., description="Durée en secondes")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        """Configuration Pydantic."""

        from_attributes = True


class ScanListResponse(BaseModel):
    """Réponse paginée de la liste des scans."""

    items: List[ScanListItem] = Field(..., description="Liste des scans")
    total: int = Field(..., description="Nombre total")
    page: int = Field(1, ge=1, description="Numéro de page")
    per_page: int = Field(20, ge=1, description="Éléments par page")
    total_pages: int = Field(0, ge=0, description="Nombre total de pages")


class ScanDetailResponse(BaseModel):
    """Détail complet d'un scan."""

    id: str = Field(..., description="UUID du scan")
    url: str = Field(..., description="URL scannée")
    scan_type: str = Field(..., description="Type de scan : frontend ou backend")
    scan_mode: str = Field(..., description="Mode de scan : passive, intrusive, destructive, custom")
    result_mode: ResultMode = Field(default="single", description="Mode du résultat : single ou multi")
    status: str = Field(..., description="Statut")
    score: int | None = Field(None, description="Note /100")
    findings: List[dict[str, Any]] = Field(default_factory=list, description="Findings")
    timestamp: str = Field(..., description="Horodatage ISO")
    duration: float = Field(..., description="Durée en secondes")
    created_at: Optional[datetime] = Field(None, description="Date de création (None si non enregistré)")
    category_summaries: Optional[List[dict[str, Any]]] = Field(
        default=None,
        description="Résumés par catégorie (checks_count, etc.)",
    )
    page_results: Optional[List[dict[str, Any]]] = Field(
        default=None,
        description="Résultats par page pour un scan multi-URL",
    )
    urls: Optional[List[str]] = Field(
        default=None,
        description="Liste des URLs scannées pour un scan multi-URL",
    )
    total_tests_count: Optional[int] = Field(
        default=None,
        description="Nombre total de tests effectués",
    )
