"""Endpoints pour les scans planifiés (monitoring continu)."""

import logging
import uuid
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.schemas.scheduled_scan import (
    ScanAlertEventResponse,
    ScanAlertHistoryListResponse,
    ScheduledScanCreateRequest,
    ScheduledScanListResponse,
    ScheduledScanResponse,
    ScheduledScanUpdateRequest,
)
from app.services.scan_alert_repository import (
    count_scan_alert_events_by_user,
    delete_scan_alert_event,
    list_scan_alert_events_by_user,
)
from app.services.scheduled_scan_repository import (
    count_scheduled_scans_by_user,
    create_scheduled_scan,
    delete_scheduled_scan,
    get_scheduled_scan_by_id,
    list_scheduled_scans_by_user,
    update_scheduled_scan,
)
from app.services.scheduled_scan_utils import compute_next_run
from app.services.user_repository import get_user_by_cognito_sub
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans – planifiés"])


async def _resolve_user_id(current_user: Dict) -> uuid.UUID:
    """Résout cognito_sub → user_id en base."""
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Impossible d'identifier l'utilisateur",
        )
    async with get_async_session() as session:
        user = await get_user_by_cognito_sub(session, cognito_sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé en base de données",
            )
        return user.id


def _to_response(scan) -> ScheduledScanResponse:
    """Convertit un ScheduledScan en ScheduledScanResponse."""
    return ScheduledScanResponse(
        id=str(scan.id),
        url=scan.url,
        frequency=scan.frequency,
        schedule_hour=scan.schedule_hour,
        schedule_minute=scan.schedule_minute,
        schedule_day_of_week=scan.schedule_day_of_week,
        schedule_day_of_month=scan.schedule_day_of_month,
        timezone=getattr(scan, "timezone", None),
        next_run_at=scan.next_run_at,
        enabled=scan.enabled,
        scan_alerts_enabled=getattr(scan, "scan_alerts_enabled", True),
        created_at=scan.created_at,
    )


@router.post("/schedule", response_model=ScheduledScanResponse)
async def create_scheduled_scan_entry(
    body: ScheduledScanCreateRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> ScheduledScanResponse:
    """Crée un scan planifié."""
    try:
        user_id = await _resolve_user_id(current_user)
        async with get_async_session() as session:
            scan = await create_scheduled_scan(
                session=session,
                user_id=user_id,
                url=body.url,
                frequency=body.frequency,
                schedule_hour=body.schedule_hour,
                schedule_minute=body.schedule_minute,
                schedule_day_of_week=body.schedule_day_of_week,
                schedule_day_of_month=body.schedule_day_of_month,
                timezone_name=body.timezone,
                scan_alerts_enabled=body.scan_alerts_enabled,
            )
            return _to_response(scan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la création du scan planifié: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du scan planifié",
        )


@router.get("/schedule", response_model=ScheduledScanListResponse)
async def list_scheduled_scans(
    current_user: Annotated[Dict, Depends(get_current_user)],
    page: int = 1,
    limit: int = 10,
) -> ScheduledScanListResponse:
    """Liste les scans planifiés de l'utilisateur (pagination)."""
    try:
        user_id = await _resolve_user_id(current_user)
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        async with get_async_session() as session:
            total = await count_scheduled_scans_by_user(session, user_id)
            scans = await list_scheduled_scans_by_user(session, user_id, limit=limit, offset=offset)
            total_pages = max((total + limit - 1) // limit, 1) if total > 0 else 0
            return ScheduledScanListResponse(
                items=[_to_response(s) for s in scans],
                total=total,
                page=page,
                per_page=limit,
                total_pages=total_pages,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération des scans planifiés: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des scans planifiés",
        )


@router.patch("/schedule/{scan_id}", response_model=ScheduledScanResponse)
async def patch_scheduled_scan(
    scan_id: str,
    body: ScheduledScanUpdateRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> ScheduledScanResponse:
    """Modifie un scan planifié (fréquence, paramètres, pause)."""
    try:
        user_id = await _resolve_user_id(current_user)
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID invalide")

        async with get_async_session() as session:
            scan = await update_scheduled_scan(
                session=session,
                scan_id=scan_uuid,
                user_id=user_id,
                frequency=body.frequency,
                schedule_hour=body.schedule_hour,
                schedule_minute=body.schedule_minute,
                schedule_day_of_week=body.schedule_day_of_week,
                schedule_day_of_month=body.schedule_day_of_month,
                timezone_name=body.timezone,
                enabled=body.enabled,
                scan_alerts_enabled=body.scan_alerts_enabled,
            )
            if not scan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scan planifié non trouvé",
                )
            # Recalculer next_run_at si fréquence ou horaire modifié
            if body.frequency is not None or body.schedule_hour is not None or body.schedule_minute is not None or body.timezone is not None:
                from datetime import datetime, timezone

                from app.services.scheduled_scan_repository import update_next_run_at

                next_run = compute_next_run(
                    from_dt=datetime.now(timezone.utc),
                    frequency=scan.frequency,
                    schedule_hour=scan.schedule_hour,
                    schedule_minute=scan.schedule_minute,
                    schedule_day_of_week=scan.schedule_day_of_week,
                    schedule_day_of_month=scan.schedule_day_of_month,
                    timezone_name=scan.timezone,
                )
                await update_next_run_at(session, scan_uuid, next_run)
                scan = await get_scheduled_scan_by_id(session, scan_uuid, user_id)
            return _to_response(scan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la modification du scan planifié: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la modification du scan planifié",
        )


@router.get("/schedule/alerts/history", response_model=ScanAlertHistoryListResponse)
async def list_scan_alert_history(
    current_user: Annotated[Dict, Depends(get_current_user)],
    page: int = 1,
    limit: int = 10,
) -> ScanAlertHistoryListResponse:
    """Liste l'historique des alertes déclenchées pour l'utilisateur (pagination)."""
    try:
        user_id = await _resolve_user_id(current_user)
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        async with get_async_session() as session:
            total = await count_scan_alert_events_by_user(session, user_id)
            events = await list_scan_alert_events_by_user(session, user_id, limit=limit, offset=offset)
            total_pages = max((total + limit - 1) // limit, 1) if total > 0 else 0
            return ScanAlertHistoryListResponse(
                items=[
                    ScanAlertEventResponse(
                        id=str(e.id),
                        url=e.url,
                        alert_type=e.alert_type,
                        email_sent=e.email_sent,
                        triggered_at=e.triggered_at,
                    )
                    for e in events
                ],
                total=total,
                page=page,
                per_page=limit,
                total_pages=total_pages,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération de l'historique des alertes: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de l'historique des alertes",
        )


@router.delete("/schedule/alerts/history/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan_alert_event_entry(
    event_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> None:
    """Supprime un événement d'alerte de l'historique."""
    try:
        user_id = await _resolve_user_id(current_user)
        try:
            event_uuid = uuid.UUID(event_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID invalide")

        async with get_async_session() as session:
            deleted = await delete_scan_alert_event(session, event_uuid, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Événement d'alerte non trouvé",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression de l'événement d'alerte: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de l'événement d'alerte",
        )


@router.delete("/schedule/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_scan_entry(
    scan_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> None:
    """Supprime un scan planifié."""
    try:
        user_id = await _resolve_user_id(current_user)
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID invalide")

        async with get_async_session() as session:
            deleted = await delete_scheduled_scan(session, scan_uuid, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scan planifié non trouvé",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression du scan planifié: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du scan planifié",
        )
