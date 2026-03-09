"""Endpoints pour l'historique des scans de posture sécurité."""

import logging
import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.schemas.scan import ScanCreateRequest, ScanDetailResponse, ScanListItem, ScanListResponse
from app.services.scan_repository import (
    count_user_scans,
    create_scan,
    delete_all_user_scans,
    delete_scan_by_id,
    get_scan_by_id,
    list_scans_by_user_id,
)
from app.services.subscription_repository import get_subscription_by_user_id
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans – historique"])


@router.post("/history", response_model=ScanDetailResponse)
async def create_scan_entry(
    body: ScanCreateRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ScanDetailResponse:
    """Enregistre un scan dans l'historique (appelé par scan-service ou frontend)."""
    try:
        async with get_async_session() as session:
            subscription = await get_subscription_by_user_id(session, user_id)
            retention = (subscription.history_retention if subscription else None) or "30"
            if retention == "none":
                # Ne pas enregistrer : retourner une réponse minimale pour compatibilité
                return ScanDetailResponse(
                    id="",
                    url=body.url,
                    scan_type=body.scan_type,
                    status=body.status,
                    score=body.score,
                    findings=body.findings,
                    timestamp=body.timestamp,
                    duration=body.duration,
                    created_at=None,
                )
            scan = await create_scan(
                session=session,
                user_id=user_id,
                url=body.url,
                scan_type=body.scan_type,
                status=body.status,
                score=body.score,
                findings=body.findings,
                timestamp=body.timestamp,
                duration=body.duration,
                category_summaries=body.category_summaries,
            )
            summaries = scan.category_summaries_json or []
            total_tests = sum(s.get("checks_count", 0) for s in summaries) if summaries else None
            return ScanDetailResponse(
                id=str(scan.id),
                url=scan.url,
                scan_type=getattr(scan, "scan_type", "frontend"),
                status=scan.status,
                score=scan.score,
                findings=scan.findings_json,
                timestamp=scan.timestamp.isoformat(),
                duration=scan.duration,
                created_at=scan.created_at,
                category_summaries=summaries or None,
                total_tests_count=total_tests,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la création du scan: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'enregistrement du scan",
        )


def _parse_optional_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse une chaîne ISO en datetime timezone-aware, ou None si vide/invalide."""
    if not value or not value.strip():
        return None
    try:
        s = value.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


@router.get("/history", response_model=ScanListResponse)
async def list_scans(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    page: int = 1,
    limit: int = 20,
    url: str | None = None,
    scan_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ScanListResponse:
    """Liste les scans de l'utilisateur (pagination). Filtres optionnels par url, scan_type et plage de dates."""
    try:
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        date_from_dt = _parse_optional_datetime(date_from)
        date_to_dt = _parse_optional_datetime(date_to)

        async with get_async_session() as session:
            total = await count_user_scans(
                session,
                user_id,
                url=url,
                scan_type=scan_type,
                date_from=date_from_dt,
                date_to=date_to_dt,
            )
            scans = await list_scans_by_user_id(
                session,
                user_id,
                limit=limit,
                offset=offset,
                url=url,
                scan_type=scan_type,
                date_from=date_from_dt,
                date_to=date_to_dt,
            )

            total_pages = max((total + limit - 1) // limit, 1) if total > 0 else 0

            return ScanListResponse(
                items=[
                    ScanListItem(
                        id=str(s.id),
                        url=s.url,
                        scan_type=getattr(s, "scan_type", "frontend"),
                        status=s.status,
                        score=s.score,
                        timestamp=s.timestamp,
                        duration=s.duration,
                        created_at=s.created_at,
                    )
                    for s in scans
                ],
                total=total,
                page=page,
                per_page=limit,
                total_pages=total_pages,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération des scans: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de l'historique",
        )


@router.get("/history/{scan_id}", response_model=ScanDetailResponse)
async def get_scan_detail(
    scan_id: str,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ScanDetailResponse:
    """Récupère le détail d'un scan."""
    try:
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de scan invalide")

        async with get_async_session() as session:
            scan = await get_scan_by_id(session, scan_uuid, user_id)
            if not scan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scan non trouvé ou n'appartient pas à l'utilisateur",
                )
            summaries = scan.category_summaries_json or []
            total_tests = sum(s.get("checks_count", 0) for s in summaries) if summaries else None
            return ScanDetailResponse(
                id=str(scan.id),
                url=scan.url,
                scan_type=getattr(scan, "scan_type", "frontend"),
                status=scan.status,
                score=scan.score,
                findings=scan.findings_json,
                timestamp=scan.timestamp.isoformat(),
                duration=scan.duration,
                created_at=scan.created_at,
                category_summaries=summaries or None,
                total_tests_count=total_tests,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération du scan: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du scan",
        )


@router.delete("/history", status_code=status.HTTP_200_OK)
async def delete_all_scans(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> dict:
    """Supprime tous les scans de l'historique de l'utilisateur."""
    try:
        async with get_async_session() as session:
            deleted_count = await delete_all_user_scans(session, user_id)
            return {"deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression de l'historique: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de l'historique",
        )


@router.delete("/history/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Supprime un scan de l'historique."""
    try:
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de scan invalide")

        async with get_async_session() as session:
            deleted = await delete_scan_by_id(session, scan_uuid, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scan non trouvé ou n'appartient pas à l'utilisateur",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression du scan: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du scan",
        )
