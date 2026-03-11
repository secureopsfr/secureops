"""Helpers communs pour les jobs asynchrones (scan/crawl)."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_job_token() -> str:
    """Génère un token opaque pour accès anonyme à un job."""
    return secrets.token_urlsafe(32)


def hash_job_token(token: str, secret: str) -> str:
    """Hash HMAC-SHA256 d'un token job."""
    digest = hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def verify_job_token(token: str, token_hash: str, secret: str) -> bool:
    """Vérifie un token en comparant son hash HMAC."""
    computed = hash_job_token(token, secret)
    return hmac.compare_digest(computed, token_hash)


def compute_retry_delay_seconds(attempt_count: int) -> int:
    """Retourne le backoff en secondes selon la tentative."""
    if attempt_count <= 1:
        return 15
    if attempt_count == 2:
        return 60
    return 180


def utc_now() -> datetime:
    """Retourne l'heure UTC timezone-aware."""
    return datetime.now(UTC)


def append_progress(
    progress_log: list[dict[str, Any]] | None,
    *,
    step: str,
    message: str,
    at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Ajoute une entrée de progression et retourne la liste complète."""
    entries = list(progress_log or [])
    ts = (at or utc_now()).isoformat()
    entries.append({"step": step, "message": message, "at": ts})
    return entries


def parse_sse_chunk(chunk: str) -> tuple[str, dict[str, Any] | str] | None:
    """Parse un chunk SSE `event:` / `data:` en tuple."""
    event = "message"
    data: dict[str, Any] | str | None = None
    for raw_line in chunk.strip().splitlines():
        line = raw_line.strip()
        if line.startswith("event: "):
            event = line[7:].strip()
        elif line.startswith("data: "):
            payload = line[6:]
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
    if data is None:
        return None
    return event, data


async def create_async_job(
    session: AsyncSession,
    *,
    model: Any,
    url: str,
    scan_type: str,
    input_json: dict[str, Any] | None,
    user_id: str | None,
    job_token_hash: str | None,
    max_attempts: int = 3,
) -> Any:
    """Create and persist a new async job row for a given model."""
    job = model(
        url=url,
        scan_type=scan_type,
        input_json=input_json,
        user_id=user_id,
        job_token_hash=job_token_hash,
        max_attempts=max_attempts,
        status="pending",
        progress_log_json=[],
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_async_job_by_id(session: AsyncSession, *, model: Any, job_id: Any) -> Any | None:
    """Return one async job by id for the provided model."""
    result = await session.execute(select(model).where(model.id == job_id))
    return result.scalar_one_or_none()


async def claim_next_async_job(session: AsyncSession, *, model: Any) -> Any | None:
    """Atomically claim the next retryable pending/failed job."""
    now = utc_now()
    stmt = (
        select(model)
        .where(
            and_(
                model.status.in_(["pending", "failed"]),
                or_(model.next_retry_at.is_(None), model.next_retry_at <= now),
                model.attempt_count < model.max_attempts,
            )
        )
        .order_by(model.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        return None
    job.status = "running"
    job.started_at = now
    job.attempt_count = int(job.attempt_count or 0) + 1
    await session.commit()
    await session.refresh(job)
    return job


async def append_async_job_progress(
    session: AsyncSession,
    *,
    job: Any,
    step: str,
    message: str,
) -> None:
    """Append one progress entry and commit immediately."""
    job.progress_log_json = append_progress(job.progress_log_json, step=step, message=message)
    job.last_step = step
    job.last_message = message
    await session.commit()


async def append_async_job_progress_batch(
    session: AsyncSession,
    *,
    job: Any,
    entries: list[dict[str, str]],
) -> None:
    """Append multiple progress entries and commit once."""
    if not entries:
        return
    current = list(job.progress_log_json or [])
    for entry in entries:
        current = append_progress(
            current,
            step=str(entry.get("step", "step")),
            message=str(entry.get("message", "")),
        )
    job.progress_log_json = current
    last = entries[-1]
    job.last_step = str(last.get("step", "step"))
    job.last_message = str(last.get("message", ""))
    await session.commit()


async def mark_async_job_completed(
    session: AsyncSession,
    *,
    job: Any,
    result_json: dict[str, Any],
) -> None:
    """Mark job completed and persist final payload."""
    job.status = "completed"
    job.result_json = result_json
    job.error_json = None
    job.completed_at = utc_now()
    await session.commit()


async def mark_async_job_failed(
    session: AsyncSession,
    *,
    job: Any,
    message: str,
    status_code: int = 500,
    error_type: str = "unexpected_error",
    retryable: bool = True,
) -> None:
    """Mark job failed and set next retry time when retryable."""
    job.error_json = {"message": message, "status_code": status_code, "error_type": error_type}
    if retryable and job.attempt_count < job.max_attempts:
        delay = compute_retry_delay_seconds(job.attempt_count)
        job.status = "failed"
        job.next_retry_at = utc_now() + timedelta(seconds=delay)
    else:
        job.status = "failed"
        job.attempt_count = job.max_attempts
        job.completed_at = utc_now()
        job.next_retry_at = None
    await session.commit()


class ProgressBatcher:
    """Batch progress entries before persisting to the database."""

    def __init__(
        self,
        *,
        append_batch: Any,
        session: Any,
        job: Any,
        batch_window_seconds: float,
    ) -> None:
        """Initialize the progress batcher."""
        self._append_batch = append_batch
        self._session = session
        self._job = job
        self._batch_window_seconds = batch_window_seconds
        self._buffer: list[dict[str, str]] = []
        self._last_flush_monotonic = time.monotonic()

    async def flush(self, *, force: bool = False) -> None:
        """Persist buffered progress entries when batch window is reached."""
        now = time.monotonic()
        if not self._buffer:
            return
        if not force and (now - self._last_flush_monotonic) < self._batch_window_seconds:
            return
        entries = self._buffer
        self._buffer = []
        await self._append_batch(self._session, self._job, entries)
        self._last_flush_monotonic = now

    async def on_progress(self, step: str, message: str) -> None:
        """Collect one progress entry and flush if needed."""
        self._buffer.append({"step": step, "message": message})
        await self.flush(force=False)
