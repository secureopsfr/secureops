"""Schémas Pydantic pour les scans planifiés."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.url_utils import URLValidationError, normalize_scan_url

FrequencyType = Literal["daily", "weekly", "monthly"]


class ScheduledScanCreateRequest(BaseModel):
    """Schéma pour la création d'un scan planifié."""

    url: str = Field(..., description="URL à scanner (http ou https, ex. https://example.com)")
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


class ScheduledScanResponse(BaseModel):
    """Réponse pour un scan planifié."""

    id: str = Field(..., description="UUID du scan planifié")
    url: str = Field(..., description="URL à scanner")
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
    alert_type: str = Field(..., description="Type : regression ou critical_finding")
    email_sent: bool = Field(..., description="True si l'email a été envoyé avec succès")
    triggered_at: datetime = Field(..., description="Date/heure du déclenchement")
