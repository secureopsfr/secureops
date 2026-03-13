"""Use-cases d'accès et d'autorisation pour jobs async scan."""

from __future__ import annotations

from typing import Any

from common.async_jobs import verify_job_token


class AsyncJobAccessError(Exception):
    """Base class for async job access errors."""


class NonFrontendAuthRequiredError(AsyncJobAccessError):
    """Raised when non-frontend job is requested without user."""


class AnonymousPassiveFrontendOnlyError(AsyncJobAccessError):
    """Raised when anonymous job is not frontend/passive."""


class JobNotFoundError(AsyncJobAccessError):
    """Raised when a requested async job does not exist."""


class JobAccessDeniedError(AsyncJobAccessError):
    """Raised when caller cannot access the requested async job."""


class JobResultNotReadyError(AsyncJobAccessError):
    """Raised when result is requested before completion."""


def require_user_for_non_frontend(scan_type: str, authenticated_user_id: str | None) -> None:
    """Ensure non-frontend scans are only allowed for authenticated users."""
    if scan_type != "frontend" and not authenticated_user_id:
        raise NonFrontendAuthRequiredError("Authentification requise pour ce type de scan")


def require_anonymous_passive_frontend_only(
    *,
    scan_type: str,
    scan_mode: str,
    authenticated_user_id: str | None,
) -> None:
    """Ensure anonymous create requests are strictly frontend + passive."""
    if authenticated_user_id:
        return
    if scan_type != "frontend" or scan_mode != "passive":
        raise AnonymousPassiveFrontendOnlyError("Sans authentification, seul le scan frontend en mode passif est autorise")


def can_access_job(
    job: Any,
    *,
    authenticated_user_id: str | None,
    job_token: str | None,
    token_secret: str,
) -> bool:
    """Return True when caller can access this async job."""
    if job.user_id:
        return bool(authenticated_user_id and authenticated_user_id == job.user_id)
    if not job.job_token_hash:
        return False
    if not job_token:
        return False
    return verify_job_token(job_token, job.job_token_hash, token_secret)


def require_existing_job(job: Any | None) -> Any:
    """Return job when present, otherwise raise not-found error."""
    if job is None:
        raise JobNotFoundError("Job introuvable")
    return job


def require_job_access(
    job: Any,
    *,
    authenticated_user_id: str | None,
    job_token: str | None,
    token_secret: str,
) -> None:
    """Ensure caller can access the job, else raise forbidden error."""
    if not can_access_job(
        job,
        authenticated_user_id=authenticated_user_id,
        job_token=job_token,
        token_secret=token_secret,
    ):
        raise JobAccessDeniedError("Accès refusé")


def require_completed_job(job: Any) -> None:
    """Ensure job result is available (status=completed)."""
    if job.status != "completed":
        raise JobResultNotReadyError("Résultat non disponible")
