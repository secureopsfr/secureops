"""Configuration des workers async scan."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class AsyncJobsSettings:
    """Paramètres async jobs pour le scan-service."""

    worker_poll_interval_seconds: float
    job_timeout_seconds: int
    max_attempts: int
    progress_batch_window_seconds: float


@lru_cache(maxsize=1)
def get_async_jobs_settings() -> AsyncJobsSettings:
    """Charge la section async_jobs depuis config/settings.yml."""
    data = _load_settings_yml()
    cfg = data.get("async_jobs") or {}
    return AsyncJobsSettings(
        worker_poll_interval_seconds=float(cfg.get("worker_poll_interval_seconds", 2.0)),
        job_timeout_seconds=int(cfg.get("job_timeout_seconds", 300)),
        max_attempts=int(cfg.get("max_attempts", 3)),
        progress_batch_window_seconds=float(cfg.get("progress_batch_window_seconds", 0.2)),
    )
