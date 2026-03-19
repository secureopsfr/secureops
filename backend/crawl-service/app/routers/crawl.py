"""Routes crawl async (DB queue + polling)."""

import os
import uuid

from common.async_jobs import generate_job_token, hash_job_token
from common.blacklist import check_blacklist
from common.url_utils import URLValidationError
from fastapi import APIRouter, Header, HTTPException

from app.config_loader import get_async_jobs_settings, get_blacklist_settings
from app.db import get_async_session
from app.schemas.async_job import CrawlAsyncCreateRequest, CrawlAsyncCreateResponse, CrawlAsyncStatusResponse
from app.services.async_job_repository import create_job, get_job_by_id
from app.use_cases.async_job_access import (
    JobAccessDeniedError,
    JobNotFoundError,
    JobResultNotReadyError,
    require_completed_job,
    require_existing_job,
    require_job_access,
)
from app.utils.url_validator import validate_and_normalize_url

router = APIRouter(prefix="/api", tags=["crawl"])
_X_AUTHENTICATED_USER_ID = Header(default=None, alias="X-Authenticated-User-Id")
_X_JOB_TOKEN = Header(default=None, alias="X-Job-Token")
ASYNC_JOB_TOKEN_SECRET = os.getenv("ASYNC_JOB_TOKEN_SECRET", "dev-async-job-secret")
ASYNC_MAX_ATTEMPTS = get_async_jobs_settings().max_attempts


@router.post("/crawl/async", response_model=CrawlAsyncCreateResponse, status_code=202)
async def create_crawl_async_job(
    body: CrawlAsyncCreateRequest,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
) -> CrawlAsyncCreateResponse:
    """Crée un job async crawl."""
    try:
        normalized_url = validate_and_normalize_url(body.url)
        await check_blacklist(normalized_url, get_blacklist_settings())
    except URLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    raw_job_token: str | None = None
    token_hash: str | None = None
    if not authenticated_user_id:
        raw_job_token = generate_job_token()
        token_hash = hash_job_token(raw_job_token, ASYNC_JOB_TOKEN_SECRET)
    try:
        async with get_async_session() as session:
            job = await create_job(
                session,
                url=normalized_url,
                input_json=body.input,
                user_id=authenticated_user_id,
                job_token_hash=token_hash,
                max_attempts=ASYNC_MAX_ATTEMPTS,
            )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Base de données indisponible")
    return CrawlAsyncCreateResponse(
        job_id=str(job.id),
        status="pending",
        scan_type="frontend",
        job_token=raw_job_token,
    )


@router.get("/crawl/async/{job_id}", response_model=CrawlAsyncStatusResponse)
async def get_crawl_async_job_status(
    job_id: str,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
    job_token: str | None = _X_JOB_TOKEN,
) -> CrawlAsyncStatusResponse:
    """Retourne le statut d'un job async crawl."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="job_id invalide")
    try:
        async with get_async_session() as session:
            job = require_existing_job(await get_job_by_id(session, job_uuid))
            require_job_access(
                job,
                authenticated_user_id=authenticated_user_id,
                job_token=job_token,
                token_secret=ASYNC_JOB_TOKEN_SECRET,
            )
            return CrawlAsyncStatusResponse(
                job_id=str(job.id),
                scan_type="frontend",
                status=job.status,  # type: ignore[arg-type]
                attempt_count=int(job.attempt_count or 0),
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                last_step=job.last_step,
                last_message=job.last_message,
                progress_log=list(job.progress_log_json or []),
                error=job.error_json,
            )
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except JobAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Base de données indisponible")


@router.get("/crawl/async/{job_id}/result")
async def get_crawl_async_job_result(
    job_id: str,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
    job_token: str | None = _X_JOB_TOKEN,
) -> dict:
    """Retourne le résultat d'un job async crawl."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="job_id invalide")
    try:
        async with get_async_session() as session:
            job = require_existing_job(await get_job_by_id(session, job_uuid))
            require_job_access(
                job,
                authenticated_user_id=authenticated_user_id,
                job_token=job_token,
                token_secret=ASYNC_JOB_TOKEN_SECRET,
            )
            require_completed_job(job)
            return dict(job.result_json or {})
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except JobAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except JobResultNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Base de données indisponible")
