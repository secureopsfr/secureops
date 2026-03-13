"""Schémas API pour les jobs async scan."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.config_loader import get_multi_scan_settings
from app.utils.url_helpers import registered_domain

ScanType = Literal["frontend", "backend", "both"]
ScanMode = Literal["passive", "intrusive", "destructive", "custom"]
JobStatus = Literal["pending", "running", "completed", "failed"]


class ScanAsyncCreateRequest(BaseModel):
    """Corps de création de job scan async (single URL)."""

    url: str = Field(..., min_length=1)
    scan_type: ScanType = "frontend"
    scan_mode: ScanMode = "passive"
    input: dict[str, Any] = Field(default_factory=dict)


class ScanAsyncMultiCreateRequest(BaseModel):
    """Corps de création de job scan multi-URL (même domaine, connecté uniquement).

    Attributes:
        urls: Liste d'URLs à scanner. Toutes doivent appartenir au même domaine.
              Minimum 2, maximum défini par multi_scan.max_urls dans settings.yml.
        scan_type: Type de scan (uniquement "frontend" en V1).
        input: Paramètres additionnels (réservé pour extensions futures).
    """

    urls: list[str] = Field(..., min_length=2)
    scan_type: ScanType = "frontend"
    scan_mode: ScanMode = "passive"
    input: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_urls(self) -> "ScanAsyncMultiCreateRequest":
        settings = get_multi_scan_settings()
        if len(self.urls) > settings.max_urls:
            raise ValueError(f"Le scan multi-URL est limité à {settings.max_urls} URLs. " f"Reçu : {len(self.urls)}.")
        # Compare registered domains (eTLD+1) so that subdomains like
        # community.finary.com and finary.com are treated as the same site.
        # Path-only URLs (empty registered_domain) are silently ignored.
        reg_domains = {registered_domain(u) for u in self.urls if u}
        reg_domains.discard("")
        if len(reg_domains) > 1:
            raise ValueError(
                f"Toutes les URLs doivent appartenir au même domaine enregistré. " f"Domaines détectés : {', '.join(sorted(reg_domains))}."
            )
        return self


class ScanAsyncCreateResponse(BaseModel):
    """Réponse à la création d'un job."""

    job_id: str
    status: JobStatus
    scan_type: ScanType
    scan_mode: ScanMode = "passive"
    job_token: str | None = None


class ScanAsyncStatusResponse(BaseModel):
    """Statut détaillé d'un job scan."""

    job_id: str
    scan_type: ScanType
    scan_mode: ScanMode = "passive"
    status: JobStatus
    result_mode: str = "single"
    attempt_count: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_step: str | None = None
    last_message: str | None = None
    progress_log: list[dict[str, Any]] = Field(default_factory=list)
    error: dict[str, Any] | None = None
