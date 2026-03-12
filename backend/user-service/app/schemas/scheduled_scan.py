"""Schémas Pydantic pour les scans planifiés."""

from datetime import datetime
from typing import List, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.utils.url_utils import URLValidationError, normalize_scan_url

FrequencyType = Literal["daily", "weekly", "monthly"]
ScanType = Literal["frontend", "backend", "custom"]
ResultMode = Literal["single", "multi"]


class ScheduledScanCreateRequest(BaseModel):
    """Schéma pour la création d'un scan planifié."""

    url: str = Field(..., description="URL à scanner (http ou https, ex. https://example.com)")
    scan_type: ScanType = Field(..., description="Type de scan : frontend, backend, custom")
    result_mode: ResultMode = Field("single", description="Mode de résultat : single ou multi")
    urls: Optional[List[str]] = Field(
        None,
        description="Liste d'URLs pour un scan multi-pages (normalisées).",
    )
    frequency: FrequencyType = Field(..., description="Fréquence : daily, weekly, monthly")
    schedule_hour: int = Field(2, ge=0, le=23, description="Heure d'exécution (0-23) dans le fuseau utilisateur")
    schedule_minute: int = Field(0, ge=0, le=59, description="Minute d'exécution (0-59)")
    schedule_day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Jour de la semaine pour weekly (0=lundi, 6=dimanche)")
    schedule_day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Jour du mois pour monthly (1-31)")
    timezone: Optional[str] = Field(None, description="Fuseau utilisateur (ex. Europe/Paris). Si null, UTC.")
    scan_alerts_enabled: bool = Field(True, description="Recevoir des emails en cas de régression ou finding critique")

    @field_validator("url")
    @classmethod
    def validate_and_normalize_url(cls, v: str) -> str:
        """Valide et normalise l'URL (schémas http/https, ajoute https:// si absent)."""
        try:
            return normalize_scan_url(v)
        except URLValidationError as e:
            raise ValueError(str(e)) from e

    @field_validator("urls")
    @classmethod
    def validate_and_normalize_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Valide et normalise la liste d'URLs si fournie."""
        if v is None:
            return None
        normalized: list[str] = []
        for raw_url in v:
            try:
                normalized.append(normalize_scan_url(raw_url))
            except URLValidationError as e:
                raise ValueError(str(e)) from e
        return normalized

    @field_validator("result_mode")
    @classmethod
    def validate_result_mode(cls, v: ResultMode) -> ResultMode:
        """Valide la valeur du mode de résultat."""
        return v

    @field_validator("urls")
    @classmethod
    def validate_urls_for_mode(cls, urls: Optional[List[str]], info) -> Optional[List[str]]:
        """Impose urls en mode multi et vérifie un même domaine racine."""
        result_mode = info.data.get("result_mode", "single")
        if result_mode == "multi":
            if not urls or len(urls) < 2:
                raise ValueError("Le mode multi nécessite au moins 2 URLs.")
            hosts = {(urlparse(u).hostname or "").replace("www.", "").lower() for u in urls}
            if len(hosts) > 1:
                raise ValueError("Toutes les URLs du scan multi doivent appartenir au même domaine.")
        return urls


class ScheduledScanUpdateRequest(BaseModel):
    """Schéma pour la mise à jour d'un scan planifié."""

    frequency: Optional[FrequencyType] = Field(None, description="Fréquence")
    schedule_hour: Optional[int] = Field(None, ge=0, le=23)
    schedule_minute: Optional[int] = Field(None, ge=0, le=59)
    schedule_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    schedule_day_of_month: Optional[int] = Field(None, ge=1, le=31)
    timezone: Optional[str] = Field(None, description="Fuseau utilisateur (ex. Europe/Paris)")
    enabled: Optional[bool] = Field(None, description="Actif ou en pause")
    scan_alerts_enabled: Optional[bool] = Field(None, description="Alertes email régression/finding critique")


class ScheduledScanListResponse(BaseModel):
    """Réponse paginée de la liste des scans planifiés."""

    items: List["ScheduledScanResponse"] = Field(..., description="Liste des scans planifiés")
    total: int = Field(..., description="Nombre total")
    page: int = Field(1, ge=1, description="Numéro de page")
    per_page: int = Field(20, ge=1, description="Éléments par page")
    total_pages: int = Field(0, ge=0, description="Nombre total de pages")


class ScheduledScanResponse(BaseModel):
    """Réponse pour un scan planifié."""

    id: str = Field(..., description="UUID du scan planifié")
    url: str = Field(..., description="URL à scanner")
    scan_type: str = Field(..., description="Type de scan : frontend, backend, custom")
    result_mode: ResultMode = Field("single", description="Mode de résultat : single ou multi")
    urls: Optional[List[str]] = Field(None, description="Liste d'URLs en mode multi-pages")
    frequency: str = Field(..., description="Fréquence")
    schedule_hour: int = Field(..., description="Heure d'exécution")
    schedule_minute: int = Field(..., description="Minute d'exécution")
    schedule_day_of_week: Optional[int] = Field(None, description="Jour de la semaine (weekly)")
    schedule_day_of_month: Optional[int] = Field(None, description="Jour du mois (monthly)")
    timezone: Optional[str] = Field(None, description="Fuseau utilisateur (ex. Europe/Paris)")
    next_run_at: datetime = Field(..., description="Prochaine exécution planifiée")
    enabled: bool = Field(..., description="Scan actif ou en pause")
    scan_alerts_enabled: bool = Field(True, description="Alertes email régression/finding critique")
    created_at: datetime = Field(..., description="Date de création")


class ScanAlertEventResponse(BaseModel):
    """Réponse pour un événement d'alerte déclenché."""

    id: str = Field(..., description="UUID de l'événement")
    url: str = Field(..., description="URL scannée")
    scan_type: str = Field(..., description="Type de scan : frontend, backend, custom")
    alert_type: str = Field(..., description="Type : regression ou critical_finding")
    email_sent: bool = Field(..., description="True si l'email a été envoyé avec succès")
    triggered_at: datetime = Field(..., description="Date/heure du déclenchement")


class ScanAlertHistoryListResponse(BaseModel):
    """Réponse paginée de l'historique des alertes."""

    items: List[ScanAlertEventResponse] = Field(..., description="Liste des événements")
    total: int = Field(..., description="Nombre total")
    page: int = Field(1, ge=1, description="Numéro de page")
    per_page: int = Field(20, ge=1, description="Éléments par page")
    total_pages: int = Field(0, ge=0, description="Nombre total de pages")
