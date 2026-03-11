"""Schémas API pour les jobs async scan."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ScanType = Literal["frontend", "backend", "custom"]
JobStatus = Literal["pending", "running", "completed", "failed"]


class ScanAsyncCreateRequest(BaseModel):
    """Corps de création de job scan async."""

    url: str = Field(..., min_length=1)
    scan_type: ScanType = "frontend"
    input: dict[str, Any] = Field(default_factory=dict)


class ScanAsyncCreateResponse(BaseModel):
    """Réponse à la création d'un job."""

    job_id: str
    status: JobStatus
    scan_type: ScanType
    job_token: str | None = None


class ScanAsyncStatusResponse(BaseModel):
    """Statut détaillé d'un job scan."""

    job_id: str
    scan_type: ScanType
    status: JobStatus
    attempt_count: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_step: str | None = None
    last_message: str | None = None
    progress_log: list[dict[str, Any]] = Field(default_factory=list)
    error: dict[str, Any] | None = None
