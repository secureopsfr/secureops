"""Route scan: export PDF, endpoint interne, et mode async."""

import logging
import os
import uuid
from urllib.parse import urljoin

import httpx
from common.async_jobs import generate_job_token, hash_job_token
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.config_loader import get_async_jobs_settings, get_external_services_settings
from app.db import get_async_session
from app.schemas.async_job import ScanAsyncCreateRequest, ScanAsyncCreateResponse, ScanAsyncMultiCreateRequest, ScanAsyncStatusResponse
from app.schemas.scan import ScanForPdfSchema
from app.services.async_job_repository import create_job, get_job_by_id
from app.services.multi_scan_orchestrator import run_multi_scan
from app.services.scan_runner import ScanRunError, run_scan_to_result
from app.use_cases.async_job_access import (
    JobAccessDeniedError,
    JobNotFoundError,
    JobResultNotReadyError,
    NonFrontendAuthRequiredError,
    require_completed_job,
    require_existing_job,
    require_job_access,
    require_user_for_non_frontend,
)
from app.utils.url_validator import URLValidationError

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


def _normalize_lang(lang: str) -> str:
    """Normalise la langue pour les libellés d'export."""
    return "en" if lang == "en" else "fr"


def _build_pages_evidence(page_urls: list[str], lang: str) -> str:
    """Construit la preuve textuelle avec les pages concernées."""
    shown_urls = page_urls[:20]
    extra = len(page_urls) - len(shown_urls)
    pages_list = ", ".join(shown_urls)
    if extra > 0:
        pages_list = f"{pages_list}, +{extra}"

    if lang == "en":
        return f"Detected on {len(page_urls)} page(s): {pages_list}"
    return f"Repéré sur {len(page_urls)} page(s): {pages_list}"


def _finding_group_key(finding: dict) -> tuple[str, str, str, str, str]:
    """Construit la clé de regroupement d'un finding."""
    return (
        str(finding.get("id", "") or ""),
        str(finding.get("category", "") or ""),
        str(finding.get("severity", "") or ""),
        str(finding.get("title", "") or ""),
        str(finding.get("recommendation", "") or ""),
    )


def _merge_references(existing: dict, incoming: dict) -> None:
    """Fusionne les références d'un finding dans la version agrégée."""
    refs = existing.get("references")
    if not isinstance(refs, list):
        refs = []
    new_refs = incoming.get("references")
    if isinstance(new_refs, list):
        refs = list(dict.fromkeys([*refs, *new_refs]))
    existing["references"] = refs


def _accumulate_page_findings(
    page: dict,
    grouped: dict[tuple[str, str, str, str, str], dict],
    page_urls_by_group: dict[tuple[str, str, str, str, str], set[str]],
) -> None:
    """Agrège les findings d'une page dans les structures de regroupement."""
    page_url = str(page.get("url", "")).strip()
    page_findings = page.get("findings") if isinstance(page.get("findings"), list) else []
    for finding in page_findings:
        if not isinstance(finding, dict):
            continue

        key = _finding_group_key(finding)
        if key not in grouped:
            grouped[key] = dict(finding)
            page_urls_by_group[key] = set()
        if page_url:
            page_urls_by_group[key].add(page_url)

        _merge_references(grouped[key], finding)


def _aggregate_multi_page_findings(page_results: list[dict], lang: str) -> list[dict]:
    """Fusionne les findings identiques détectées sur plusieurs pages.

    Les findings sont regroupées par (id, category, severity, title, recommendation).
    Les URLs de pages touchées sont listées dans la preuve pour réduire la répétition
    dans le sommaire et les sections PDF.
    """
    grouped: dict[tuple[str, str, str, str, str], dict] = {}
    page_urls_by_group: dict[tuple[str, str, str, str, str], set[str]] = {}

    for page in page_results:
        if not isinstance(page, dict):
            continue
        _accumulate_page_findings(page, grouped, page_urls_by_group)

    merged_findings: list[dict] = []
    for key, finding in grouped.items():
        page_urls = sorted(page_urls_by_group.get(key, set()))
        if page_urls:
            original_evidence = str(finding.get("evidence", "") or "").strip()
            page_evidence = _build_pages_evidence(page_urls, lang)
            finding["evidence"] = f"{page_evidence}\n{original_evidence}" if original_evidence else page_evidence
        merged_findings.append(finding)

    return merged_findings


def _build_pdf_payload_from_history_scan(
    data: dict,
    lang: str = "fr",
) -> tuple[dict | None, str | None]:
    """Construit le payload PDF depuis un scan d'historique (single ou multi)."""
    result_mode = data.get("result_mode", "single")
    if result_mode != "multi":
        return (
            {
                "url": data.get("url"),
                "score": data.get("score"),
                "timestamp": data.get("timestamp", ""),
                "duration": data.get("duration", 0.0),
                "findings": data.get("findings", []),
            },
            None,
        )

    page_results = data.get("page_results")
    urls = data.get("urls")
    if not isinstance(page_results, list) or not isinstance(urls, list) or len(page_results) == 0 or len(urls) == 0:
        return None, "Export PDF indisponible: données multi-pages incomplètes dans l'historique."

    findings = _aggregate_multi_page_findings(page_results, _normalize_lang(lang))

    return (
        {
            "url": data.get("url"),
            "score": data.get("score"),
            "timestamp": data.get("timestamp", ""),
            "duration": data.get("duration", 0.0),
            "findings": findings,
            "result_mode": "multi",
            "page_results": page_results,
        },
        None,
    )


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
    authorization = request.headers.get("Authorization")
    if not authorization:
        return Response(status_code=401, content="Authentification requise")

    url = urljoin(f"{GATEWAY_URL.rstrip('/')}/", f"user/api/scans/history/{scan_id}")
    headers = {"Authorization": authorization}

    async with httpx.AsyncClient(timeout=FETCH_SCAN_TIMEOUT) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            return Response(status_code=404, content="Scan non trouvé")
        if resp.status_code == 401:
            return Response(status_code=401, content="Authentification requise")
        if resp.status_code >= 400:
            logger.warning("Erreur récupération scan pour PDF: %s %s", resp.status_code, resp.text[:200])
            return Response(status_code=502, content="Impossible de récupérer le scan")

    data = resp.json()
    payload_data, payload_error = _build_pdf_payload_from_history_scan(
        data,
        lang=_normalize_lang(lang),
    )
    if payload_error:
        return Response(status_code=409, content=payload_error)

    try:
        scan_data = ScanForPdfSchema.model_validate(payload_data)
    except Exception as e:
        logger.warning("Schéma scan invalide pour PDF: %s", e)
        return Response(status_code=502, content="Données du scan invalides")

    pdf_endpoint = urljoin(f"{PDF_SERVICE_URL.rstrip('/')}/", "api/report/pdf")
    payload = {
        "url": scan_data.url,
        "score": scan_data.score,
        "timestamp": scan_data.timestamp,
        "duration": scan_data.duration,
        "findings": scan_data.findings,
        "result_mode": payload_data.get("result_mode"),
        "page_results": payload_data.get("page_results"),
    }
    params = {"lang": lang if lang in ("fr", "en") else "fr", "include_matrices": include_matrices}
    pdf_headers = {}
    if PDF_SERVICE_INTERNAL_API_KEY:
        pdf_headers["X-Internal-Api-Key"] = PDF_SERVICE_INTERNAL_API_KEY

    async with httpx.AsyncClient(timeout=PDF_REQUEST_TIMEOUT) as client:
        pdf_resp = await client.post(pdf_endpoint, json=payload, params=params, headers=pdf_headers)
        if pdf_resp.status_code >= 400:
            logger.warning("Erreur pdf-service pour export PDF: %s %s", pdf_resp.status_code, pdf_resp.text[:200])
            return Response(status_code=502, content="Impossible de générer le PDF")

    pdf_bytes = pdf_resp.content
    host = scan_data.url.replace("https://", "").replace("http://", "").split("/")[0][:30]
    filename = f"scan-{host}-{scan_data.timestamp[:10]}.pdf".replace(":", "-")

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


class InternalMultiScanRequest(BaseModel):
    """Requête pour l'endpoint interne multi (scheduler)."""

    urls: list[str] = Field(..., min_length=2, description="Liste d'URLs d'un même domaine")


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
        return await run_scan_to_result(body.url)
    except URLValidationError as e:
        return {"status": "error", "message": str(e), "status_code": 400}
    except ScanRunError as e:
        return {"status": "error", "message": e.message, "status_code": e.status_code}
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
        result = await run_multi_scan(body.urls)
        return result.to_dict()
    except URLValidationError as e:
        return {"status": "error", "message": str(e), "status_code": 400}
    except ValueError as e:
        return {"status": "error", "message": str(e), "status_code": 400}
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
    except NonFrontendAuthRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    raw_job_token: str | None = None
    token_hash: str | None = None
    if not authenticated_user_id:
        raw_job_token = generate_job_token()
        token_hash = hash_job_token(raw_job_token, ASYNC_JOB_TOKEN_SECRET)
    try:
        async with get_async_session() as session:
            job = await create_job(
                session,
                url=body.url,
                scan_type=body.scan_type,
                input_json=body.input,
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
        async with get_async_session() as session:
            job = await create_job(
                session,
                url=body.urls[0],
                scan_type=body.scan_type,
                input_json={"urls": body.urls, **body.input},
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
