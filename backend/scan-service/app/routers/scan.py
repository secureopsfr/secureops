"""Route scan: export PDF, endpoint interne, et mode async."""

import logging
import os
import uuid

from common.async_jobs import generate_job_token, hash_job_token
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.config_loader import get_async_jobs_settings, get_external_services_settings
from app.db import get_async_session
from app.schemas.async_job import ScanAsyncCreateRequest, ScanAsyncCreateResponse, ScanAsyncMultiCreateRequest, ScanAsyncStatusResponse
from app.services.async_job_repository import create_job, get_job_by_id
from app.services.async_scan_executor import execute_multi_scan_job, execute_scan_job
from app.services.pdf_export_service import PdfExportError, export_scan_pdf_bytes
from app.use_cases.async_job_access import (
    AnonymousPassiveFrontendOnlyError,
    JobAccessDeniedError,
    JobNotFoundError,
    JobResultNotReadyError,
    NonFrontendAuthRequiredError,
    require_anonymous_passive_frontend_only,
    require_completed_job,
    require_existing_job,
    require_job_access,
    require_user_for_non_frontend,
)

# Clé API pour les appels service-to-service (endpoint interne).
# Si définie, le header X-Internal-Api-Key doit correspondre.
INTERNAL_API_KEY = os.getenv("SCAN_SERVICE_INTERNAL_API_KEY")

_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie la clé API interne si SCAN_SERVICE_INTERNAL_API_KEY est définie.

    En dev (variable non définie), l'accès est autorisé sans clé.
    """
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY_INTERNAL_API_KEY = Depends(_verify_internal_api_key)
_X_AUTHENTICATED_USER_ID = Header(default=None, alias="X-Authenticated-User-Id")
_X_JOB_TOKEN = Header(default=None, alias="X-Job-Token")


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scan"])

PDF_SERVICE_INTERNAL_API_KEY = os.getenv("PDF_SERVICE_INTERNAL_API_KEY")
_EXTERNAL = get_external_services_settings()
GATEWAY_URL = os.getenv("GATEWAY_URL", _EXTERNAL.gateway_url)
PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", _EXTERNAL.pdf_service_url)
FETCH_SCAN_TIMEOUT = _EXTERNAL.fetch_scan_timeout
PDF_REQUEST_TIMEOUT = _EXTERNAL.pdf_request_timeout
ASYNC_JOB_TOKEN_SECRET = os.getenv("ASYNC_JOB_TOKEN_SECRET", "dev-async-job-secret")
ASYNC_MAX_ATTEMPTS = get_async_jobs_settings().max_attempts


@router.get(
    "/scan/export/pdf",
    summary="Exporter un scan en PDF",
    description="Génère un rapport PDF pour un scan sauvegardé. Auth requise.",
)
async def export_scan_pdf(
    request: Request,
    scan_id: str,
    include_matrices: bool = True,
    lang: str = "fr",
) -> Response:
    """Récupère le scan depuis user-service et génère le PDF."""
    try:
        pdf_bytes, filename = await export_scan_pdf_bytes(
            authorization=request.headers.get("Authorization"),
            scan_id=scan_id,
            include_matrices=include_matrices,
            lang=lang,
            gateway_url=GATEWAY_URL,
            pdf_service_url=PDF_SERVICE_URL,
            fetch_scan_timeout=FETCH_SCAN_TIMEOUT,
            pdf_request_timeout=PDF_REQUEST_TIMEOUT,
            pdf_service_internal_api_key=PDF_SERVICE_INTERNAL_API_KEY,
        )
    except PdfExportError as exc:
        return Response(status_code=exc.status_code, content=exc.message)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


class InternalScanRequest(BaseModel):
    """Requête pour l'endpoint interne (scheduler)."""

    url: str = Field(..., description="URL à scanner")
    scan_type: str = Field("frontend", description="Type de scan: frontend ou backend")
    scan_mode: str = Field("passive", description="Mode de scan: passive, intrusive, destructive, custom")


class InternalMultiScanRequest(BaseModel):
    """Requête pour l'endpoint interne multi (scheduler)."""

    urls: list[str] = Field(..., min_length=2, description="Liste d'URLs d'un même domaine")
    scan_type: str = Field("frontend", description="Type de scan: frontend ou backend")
    scan_mode: str = Field("passive", description="Mode de scan: passive, intrusive, destructive, custom")


@router.post(
    "/internal/scan/run",
    summary="[Interne] Exécuter un scan et retourner le résultat en JSON",
    description="Utilisé par le scheduler user-service. Si SCAN_SERVICE_INTERNAL_API_KEY est définie, " "le header X-Internal-Api-Key est requis.",
)
async def internal_run_scan(
    body: InternalScanRequest,
    _: None = _VERIFY_INTERNAL_API_KEY,
) -> dict:
    """Exécute le scan et retourne le résultat en JSON (pas de SSE)."""
    try:
        result_payload, error_payload = await execute_scan_job(
            url=body.url,
            scan_type=body.scan_type,
            scan_mode=body.scan_mode,
        )
        if error_payload:
            return {
                "status": "error",
                "message": error_payload.get("message", "Erreur de scan interne"),
                "status_code": int(error_payload.get("status_code", 500)),
                "error_type": error_payload.get("error_type", "unexpected_error"),
            }
        if result_payload is None:
            return {"status": "error", "message": "Résultat de scan introuvable.", "status_code": 500}
        return result_payload
    except Exception as e:
        logger.exception("Erreur inattendue lors du scan interne: %s", e)
        return {"status": "error", "message": str(e), "status_code": 500}


@router.post(
    "/internal/scan/run-multi",
    summary="[Interne] Exécuter un scan multi et retourner le résultat JSON",
    description="Utilisé par le scheduler user-service pour les scans multi-pages.",
)
async def internal_run_multi_scan(
    body: InternalMultiScanRequest,
    _: None = _VERIFY_INTERNAL_API_KEY,
) -> dict:
    """Exécute un scan multi et retourne le résultat agrégé en JSON."""
    try:
        result_payload, error_payload = await execute_multi_scan_job(
            urls=body.urls,
            scan_type=body.scan_type,
            scan_mode=body.scan_mode,
        )
        if error_payload:
            return {
                "status": "error",
                "message": error_payload.get("message", "Erreur de scan multi interne"),
                "status_code": int(error_payload.get("status_code", 500)),
                "error_type": error_payload.get("error_type", "unexpected_error"),
            }
        if result_payload is None:
            return {"status": "error", "message": "Résultat de scan multi introuvable.", "status_code": 500}
        return result_payload
    except Exception as e:
        logger.exception("Erreur inattendue lors du scan multi interne: %s", e)
        return {"status": "error", "message": str(e), "status_code": 500}


@router.post("/scan/async", response_model=ScanAsyncCreateResponse, status_code=202)
async def create_scan_async_job(
    body: ScanAsyncCreateRequest,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
) -> ScanAsyncCreateResponse:
    """Crée un job async scan et retourne immédiatement un job_id."""
    try:
        require_user_for_non_frontend(body.scan_type, authenticated_user_id)
        require_anonymous_passive_frontend_only(
            scan_type=body.scan_type,
            scan_mode=body.scan_mode,
            authenticated_user_id=authenticated_user_id,
        )
    except NonFrontendAuthRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except AnonymousPassiveFrontendOnlyError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    raw_job_token: str | None = None
    token_hash: str | None = None
    if not authenticated_user_id:
        raw_job_token = generate_job_token()
        token_hash = hash_job_token(raw_job_token, ASYNC_JOB_TOKEN_SECRET)
    job_input = {"scan_mode": body.scan_mode, **(body.input or {})}
    try:
        async with get_async_session() as session:
            job = await create_job(
                session,
                url=body.url,
                scan_type=body.scan_type,
                input_json=job_input,
                user_id=authenticated_user_id,
                job_token_hash=token_hash,
                max_attempts=ASYNC_MAX_ATTEMPTS,
            )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Base de données indisponible")
    except SQLAlchemyError as exc:
        logger.exception("Erreur création job async scan: %s", exc)
        raise HTTPException(status_code=500, detail="Impossible de créer le job")
    return ScanAsyncCreateResponse(
        job_id=str(job.id),
        status="pending",
        scan_type=body.scan_type,
        scan_mode=body.scan_mode,
        job_token=raw_job_token,
    )


@router.post("/scan/multi-async", response_model=ScanAsyncCreateResponse, status_code=202)
async def create_multi_scan_async_job(
    body: ScanAsyncMultiCreateRequest,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
) -> ScanAsyncCreateResponse:
    """Crée un job de scan multi-URL (même domaine) et retourne immédiatement un job_id.

    Nécessite une authentification. Les URLs doivent appartenir au même domaine.
    Le résultat (résultat_mode: "multi") est récupérable via GET /scan/async/{job_id}/result.
    """
    if not authenticated_user_id:
        raise HTTPException(status_code=401, detail="Authentification requise pour le scan multi-URL")

    try:
        job_input = {"scan_mode": body.scan_mode, "urls": body.urls, **(body.input or {})}
        async with get_async_session() as session:
            job = await create_job(
                session,
                url=body.urls[0],
                scan_type=body.scan_type,
                input_json=job_input,
                user_id=authenticated_user_id,
                job_token_hash=None,
                max_attempts=ASYNC_MAX_ATTEMPTS,
                result_mode="multi",
            )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Base de données indisponible")
    except SQLAlchemyError as exc:
        logger.exception("Erreur création job async multi-scan: %s", exc)
        raise HTTPException(status_code=500, detail="Impossible de créer le job")

    return ScanAsyncCreateResponse(
        job_id=str(job.id),
        status="pending",
        scan_type=body.scan_type,
        scan_mode=body.scan_mode,
        job_token=None,
    )


@router.get("/scan/async/{job_id}", response_model=ScanAsyncStatusResponse)
async def get_scan_async_job_status(
    job_id: str,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
    job_token: str | None = _X_JOB_TOKEN,
) -> ScanAsyncStatusResponse:
    """Retourne le statut d'un job async scan."""
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
            return ScanAsyncStatusResponse(
                job_id=str(job.id),
                scan_type=job.scan_type,  # type: ignore[arg-type]
                scan_mode=((getattr(job, "input_json", None) or {}).get("scan_mode") or "passive"),  # type: ignore[arg-type]
                status=job.status,  # type: ignore[arg-type]
                result_mode=getattr(job, "result_mode", "single") or "single",
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


@router.get("/scan/async/{job_id}/result")
async def get_scan_async_job_result(
    job_id: str,
    authenticated_user_id: str | None = _X_AUTHENTICATED_USER_ID,
    job_token: str | None = _X_JOB_TOKEN,
) -> dict:
    """Retourne le résultat d'un job async scan."""
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
