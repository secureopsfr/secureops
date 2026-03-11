"""Repository DB pour jobs async crawl."""

from __future__ import annotations

import uuid
from typing import Any

from common.async_jobs import (
    append_async_job_progress,
    append_async_job_progress_batch,
    claim_next_async_job,
    create_async_job,
    get_async_job_by_id,
    mark_async_job_completed,
    mark_async_job_failed,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import CrawlAsyncJob


async def create_job(
    session: AsyncSession,
    *,
    url: str,
    scan_type: str,
    input_json: dict[str, Any] | None,
    user_id: str | None,
    job_token_hash: str | None,
    max_attempts: int = 3,
) -> CrawlAsyncJob:
    """Create and persist a new asynchronous crawl job."""
    return await create_async_job(
        session,
        model=CrawlAsyncJob,
        url=url,
        scan_type=scan_type,
        input_json=input_json,
        user_id=user_id,
        job_token_hash=job_token_hash,
        max_attempts=max_attempts,
    )


async def get_job_by_id(session: AsyncSession, job_id: uuid.UUID) -> CrawlAsyncJob | None:
    """Return a crawl job by id, or None when absent."""
    return await get_async_job_by_id(session, model=CrawlAsyncJob, job_id=job_id)


async def claim_next_job(session: AsyncSession) -> CrawlAsyncJob | None:
    """Atomically claim the next available job for execution."""
    return await claim_next_async_job(session, model=CrawlAsyncJob)


async def append_job_progress(session: AsyncSession, job: CrawlAsyncJob, *, step: str, message: str) -> None:
    """Append a single progress entry and persist it immediately."""
    await append_async_job_progress(session, job=job, step=step, message=message)


async def append_job_progress_batch(
    session: AsyncSession,
    job: CrawlAsyncJob,
    entries: list[dict[str, str]],
) -> None:
    """Ajoute plusieurs entrées de progression et commit une seule fois."""
    await append_async_job_progress_batch(session, job=job, entries=entries)


async def mark_completed(session: AsyncSession, job: CrawlAsyncJob, result_json: dict[str, Any]) -> None:
    """Mark a crawl job as completed and store final result payload."""
    await mark_async_job_completed(session, job=job, result_json=result_json)


async def mark_failed(
    session: AsyncSession,
    job: CrawlAsyncJob,
    *,
    message: str,
    status_code: int = 500,
    error_type: str = "unexpected_error",
    retryable: bool = True,
) -> None:
    """Mark a crawl job as failed and schedule retry when eligible."""
    await mark_async_job_failed(
        session,
        job=job,
        message=message,
        status_code=status_code,
        error_type=error_type,
        retryable=retryable,
    )
