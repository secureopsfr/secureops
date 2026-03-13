"""Worker de consommation des jobs async scan (DB queue)."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from common.async_jobs import ProgressBatcher, utc_now

from app.config_loader import get_async_jobs_settings
from app.db import get_async_session, init_db
from app.services.async_job_repository import append_job_progress_batch, claim_next_job, mark_completed, mark_failed, mark_failed_timeout
from app.services.async_scan_executor import execute_multi_scan_job, execute_scan_job

logger = logging.getLogger(__name__)

_ASYNC = get_async_jobs_settings()
POLL_INTERVAL_SECONDS = _ASYNC.worker_poll_interval_seconds
JOB_TIMEOUT_SECONDS = _ASYNC.job_timeout_seconds
PROGRESS_BATCH_WINDOW_SECONDS = _ASYNC.progress_batch_window_seconds


async def _append_batch(session: Any, job: Any, entries: list[dict[str, Any]]) -> None:
    await append_job_progress_batch(session, job, entries=entries)


async def _mark_failure_from_error(session: Any, job: Any, error: dict[str, Any]) -> None:
    await mark_failed(
        session,
        job,
        message=str(error.get("message", "Erreur scan")),
        status_code=int(error.get("status_code", 500)),
        error_type=str(error.get("error_type", "scan_error")),
        retryable=True,
    )


async def _mark_empty_result(session: Any, job: Any) -> None:
    await mark_failed(
        session,
        job,
        message="Aucun résultat produit",
        status_code=500,
        error_type="empty_result",
        retryable=True,
    )


async def _mark_unexpected_failure(session: Any, job: Any, exc: Exception) -> None:
    await mark_failed(
        session,
        job,
        message=str(exc),
        status_code=500,
        error_type="unexpected_error",
        retryable=True,
    )


async def _finalize_job(
    session: Any,
    job: Any,
    *,
    started_at: Any,
    result: dict[str, Any] | None,
    error: dict[str, Any] | None,
) -> None:
    if utc_now() - started_at > timedelta(seconds=JOB_TIMEOUT_SECONDS):
        await mark_failed_timeout(session, job)
        return
    if error:
        await _mark_failure_from_error(session, job, error)
        return
    if result:
        await mark_completed(session, job, result)
        return
    await _mark_empty_result(session, job)


async def _execute_claimed_job(session: Any, job: Any) -> None:
    started_at = utc_now()
    progress = ProgressBatcher(
        append_batch=_append_batch,
        session=session,
        job=job,
        batch_window_seconds=PROGRESS_BATCH_WINDOW_SECONDS,
    )
    try:
        result_mode = getattr(job, "result_mode", "single") or "single"
        if result_mode == "multi":
            input_data = job.input_json or {}
            urls = input_data.get("urls") or [job.url]
            scan_mode = str(input_data.get("scan_mode") or "passive")
            result, error = await execute_multi_scan_job(
                urls=urls,
                scan_type=job.scan_type,
                scan_mode=scan_mode,
                on_progress=progress.on_progress,
            )
        else:
            input_data = job.input_json or {}
            result, error = await execute_scan_job(
                url=job.url,
                scan_type=job.scan_type,
                scan_mode=str(input_data.get("scan_mode") or "passive"),
                input_json=input_data,
                on_progress=progress.on_progress,
                flush_fn=lambda: progress.flush(force=True),
            )
        await progress.flush(force=True)
        await _finalize_job(
            session,
            job,
            started_at=started_at,
            result=result,
            error=error,
        )
    except Exception as exc:
        logger.exception("scan-worker: unexpected failure job=%s", job.id)
        await progress.flush(force=True)
        await _mark_unexpected_failure(session, job, exc)


async def _run_once() -> bool:
    """Process at most one scan async job from the queue."""
    async with get_async_session() as session:
        job = await claim_next_job(session)
        if not job:
            return False
        logger.info("scan-worker: job claimed id=%s type=%s attempt=%s", job.id, job.scan_type, job.attempt_count)
        await _execute_claimed_job(session, job)
        return True


async def main() -> None:
    """Run the scan worker loop indefinitely."""
    logging.basicConfig(level=logging.INFO)
    db_ok = await init_db()
    if not db_ok:
        raise RuntimeError("DATABASE_URL manquante pour scan-worker")
    while True:
        did_work = await _run_once()
        if not did_work:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
