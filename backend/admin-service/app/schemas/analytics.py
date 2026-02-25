"""Schémas Pydantic pour les événements analytics et les réponses d'agrégation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────── Ingestion ───────────────────────


class AnalyticsEventCreate(BaseModel):
    """Requête de création d'un événement analytics (envoyé par le frontend)."""

    session_id: str = Field(..., min_length=1, max_length=64, alias="sessionId", description="Identifiant de session (UUID côté client)")
    user_id_hash: Optional[str] = Field(None, max_length=128, alias="userIdHash", description="Hash HMAC-SHA256 de l'identifiant utilisateur")
    event_type: str = Field(
        ...,
        min_length=1,
        max_length=32,
        alias="eventType",
        description="Type d'événement (page_view, page_exit, session_start, click, scroll_depth)",
    )
    page: str = Field(..., min_length=1, max_length=512, description="Chemin de la page")
    referrer: Optional[str] = Field(None, max_length=512, description="Referrer HTTP")
    duration_ms: Optional[float] = Field(None, ge=0, alias="durationMs", description="Durée sur la page en ms")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Données additionnelles (scroll_depth, click_target…)")
    viewport: Optional[str] = Field(None, max_length=32, description="Dimensions du viewport (ex: 1920x1080)")
    device_type: Optional[str] = Field(None, max_length=16, alias="deviceType", description="Type d'appareil (desktop, mobile, tablet)")
    language: Optional[str] = Field(None, max_length=16, description="Langue du navigateur (ex: fr-FR)")
    country: Optional[str] = Field(None, max_length=2, description="Code pays ISO 3166-1 alpha-2 (ex: FR)")
    region: Optional[str] = Field(None, max_length=100, description="Région/département")
    city: Optional[str] = Field(None, max_length=100, description="Ville")
    timestamp: Optional[datetime] = Field(None, description="Horodatage de l'événement côté client (UTC)")

    model_config = ConfigDict(populate_by_name=True)


class AnalyticsIngestRequest(BaseModel):
    """Requête d'ingestion d'un batch d'événements analytics."""

    events: List[AnalyticsEventCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Batch d'événements à ingérer (max 50 par requête)",
    )

    model_config = ConfigDict(populate_by_name=True)


class AnalyticsIngestResponse(BaseModel):
    """Réponse après l'ingestion d'un batch."""

    success: bool = Field(True, description="Indique si l'opération a réussi")
    count: int = Field(..., description="Nombre d'événements enregistrés")


# ─────────────────────── Consultation ───────────────────────


class PageViewSummary(BaseModel):
    """Résumé des vues pour une page."""

    page: str = Field(..., description="Chemin de la page")
    views: int = Field(..., description="Nombre total de vues")
    unique_visitors: int = Field(..., serialization_alias="uniqueVisitors", description="Nombre de visiteurs uniques (sessions distinctes)")
    avg_duration_ms: float | None = Field(None, serialization_alias="avgDurationMs", description="Durée moyenne sur la page (ms)")
    bounce_count: int = Field(0, serialization_alias="bounceCount", description="Nombre de rebonds (sessions avec 1 seule page vue)")

    model_config = ConfigDict(populate_by_name=True)


class PageViewsSummaryResponse(BaseModel):
    """Réponse contenant les métriques de vues par page."""

    pages: List[PageViewSummary] = Field(default_factory=list, description="Liste des pages avec leurs métriques")
    total_views: int = Field(0, serialization_alias="totalViews", description="Nombre total de vues")
    total_unique_visitors: int = Field(0, serialization_alias="totalUniqueVisitors", description="Nombre total de visiteurs uniques")
    avg_pages_per_session: float | None = Field(None, serialization_alias="avgPagesPerSession", description="Nombre moyen de pages par session")
    avg_session_duration_ms: float | None = Field(None, serialization_alias="avgSessionDurationMs", description="Durée moyenne d'une session (ms)")
    bounce_rate: float | None = Field(None, serialization_alias="bounceRate", description="Taux de rebond global (0-1)")

    model_config = ConfigDict(populate_by_name=True)


class ReferrerSummary(BaseModel):
    """Résumé du trafic par referrer."""

    referrer: str = Field(..., description="Referrer source")
    count: int = Field(..., description="Nombre de visites depuis ce referrer")
    unique_visitors: int = Field(..., serialization_alias="uniqueVisitors", description="Visiteurs uniques depuis ce referrer")

    model_config = ConfigDict(populate_by_name=True)


class ReferrersSummaryResponse(BaseModel):
    """Réponse contenant le trafic par referrer."""

    referrers: List[ReferrerSummary] = Field(default_factory=list, description="Liste des referrers")

    model_config = ConfigDict(populate_by_name=True)


class TrafficTimeSeriesPoint(BaseModel):
    """Un point dans la série temporelle de trafic."""

    timestamp: datetime = Field(..., description="Horodatage du début du bucket (UTC)")
    views: int = Field(..., description="Nombre de vues dans ce bucket")
    unique_visitors: int = Field(..., serialization_alias="uniqueVisitors", description="Visiteurs uniques dans ce bucket")

    model_config = ConfigDict(populate_by_name=True)


class TrafficTimeSeriesResponse(BaseModel):
    """Réponse contenant la série temporelle de trafic."""

    bucket_minutes: int = Field(..., serialization_alias="bucketMinutes", description="Taille du bucket en minutes")
    points: List[TrafficTimeSeriesPoint] = Field(default_factory=list, description="Points de la série temporelle")

    model_config = ConfigDict(populate_by_name=True)


class DeviceBreakdown(BaseModel):
    """Répartition par type d'appareil."""

    device_type: str = Field(..., serialization_alias="deviceType", description="Type d'appareil")
    count: int = Field(..., description="Nombre de sessions")
    percentage: float = Field(..., description="Pourcentage du total (0-100)")

    model_config = ConfigDict(populate_by_name=True)


class DeviceBreakdownResponse(BaseModel):
    """Réponse contenant la répartition par appareil."""

    devices: List[DeviceBreakdown] = Field(default_factory=list, description="Répartition par appareil")

    model_config = ConfigDict(populate_by_name=True)


# ─────────────────────── Géolocalisation ───────────────────────


class GeoBreakdown(BaseModel):
    """Répartition par pays."""

    country: str = Field(..., description="Code pays ISO 3166-1 alpha-2")
    count: int = Field(..., description="Nombre de sessions")
    percentage: float = Field(..., description="Pourcentage du total (0-100)")

    model_config = ConfigDict(populate_by_name=True)


class GeoRegionBreakdown(BaseModel):
    """Répartition par région dans un pays."""

    region: str = Field(..., description="Nom de la région")
    count: int = Field(..., description="Nombre de sessions")
    percentage: float = Field(..., description="Pourcentage du total (0-100)")

    model_config = ConfigDict(populate_by_name=True)


class GeoCityBreakdown(BaseModel):
    """Répartition par ville."""

    city: str = Field(..., description="Nom de la ville")
    country: str = Field(..., description="Code pays")
    count: int = Field(..., description="Nombre de sessions")
    percentage: float = Field(..., description="Pourcentage du total (0-100)")

    model_config = ConfigDict(populate_by_name=True)


class GeoBreakdownResponse(BaseModel):
    """Réponse contenant la répartition géographique complète."""

    countries: List[GeoBreakdown] = Field(default_factory=list, description="Répartition par pays")
    regions: List[GeoRegionBreakdown] = Field(default_factory=list, description="Répartition par région")
    cities: List[GeoCityBreakdown] = Field(default_factory=list, description="Répartition par ville")

    model_config = ConfigDict(populate_by_name=True)
