"""Schémas API pour jobs async crawl."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ScanType = Literal["frontend"]
JobStatus = Literal["pending", "running", "completed", "failed"]


class CrawlAsyncCreateRequest(BaseModel):
    """Corps de création de job crawl."""

    url: str = Field(..., min_length=1)
    scan_type: ScanType = "frontend"
    input: dict[str, Any] = Field(default_factory=dict)


class CrawlAsyncCreateResponse(BaseModel):
    """Réponse création job."""

    job_id: str
    status: JobStatus
    scan_type: ScanType
    job_token: str | None = None


class CrawlAsyncStatusResponse(BaseModel):
    """Statut détaillé d'un job crawl."""

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
