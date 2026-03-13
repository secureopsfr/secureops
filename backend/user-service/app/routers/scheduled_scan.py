"""Endpoints pour les scans planifiés (monitoring continu)."""

import logging
import uuid
from datetime import datetime
from typing import Annotated, Optional

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
from app.services.scan_alert_repository import count_scan_alert_events_by_user, delete_scan_alert_event, list_scan_alert_events_by_user
from app.services.scheduled_scan_repository import (
    count_scheduled_scans_by_user,
    create_scheduled_scan,
    delete_scheduled_scan,
    get_scheduled_scan_by_id,
    list_scheduled_scans_by_user,
    update_scheduled_scan,
)
from app.services.scheduled_scan_utils import compute_next_run
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans – planifiés"])


def _to_response(scan) -> ScheduledScanResponse:
    """Convertit un ScheduledScan en ScheduledScanResponse."""
    return ScheduledScanResponse(
        id=str(scan.id),
        url=scan.url,
        scan_type=getattr(scan, "scan_type", "frontend"),
        scan_mode=getattr(scan, "scan_mode", "passive"),
        result_mode=getattr(scan, "result_mode", "single"),
        urls=getattr(scan, "urls_json", None),
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ScheduledScanResponse:
    """Crée un scan planifié."""
    try:
        async with get_async_session() as session:
            scan = await create_scheduled_scan(
                session=session,
                user_id=user_id,
                url=body.url,
                scan_type=body.scan_type,
                scan_mode=body.scan_mode,
                result_mode=body.result_mode,
                urls=body.urls,
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Erreur lors de la création du scan planifié: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du scan planifié",
        )


@router.get("/schedule", response_model=ScheduledScanListResponse)
async def list_scheduled_scans(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    page: int = 1,
    limit: int = 10,
    url: str | None = None,
    scan_type: str | None = None,
    scan_mode: str | None = None,
) -> ScheduledScanListResponse:
    """Liste les scans planifiés de l'utilisateur (pagination). Filtre optionnel par url."""
    try:
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        async with get_async_session() as session:
            total = await count_scheduled_scans_by_user(
                session,
                user_id,
                url=url,
                scan_type=scan_type,
                scan_mode=scan_mode,
            )
            scans = await list_scheduled_scans_by_user(
                session,
                user_id,
                limit=limit,
                offset=offset,
                url=url,
                scan_type=scan_type,
                scan_mode=scan_mode,
            )
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ScheduledScanResponse:
    """Modifie un scan planifié (fréquence, paramètres, pause)."""
    try:
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Erreur lors de la modification du scan planifié: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la modification du scan planifié",
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


@router.get("/schedule/alerts/history", response_model=ScanAlertHistoryListResponse)
async def list_scan_alert_history(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    page: int = 1,
    limit: int = 10,
    url: str | None = None,
    scan_type: str | None = None,
    scan_mode: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ScanAlertHistoryListResponse:
    """Liste l'historique des alertes déclenchées pour l'utilisateur (pagination). Filtres optionnels par url et plage de dates."""
    try:
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        date_from_dt = _parse_optional_datetime(date_from)
        date_to_dt = _parse_optional_datetime(date_to)
        async with get_async_session() as session:
            total = await count_scan_alert_events_by_user(
                session,
                user_id,
                url=url,
                scan_type=scan_type,
                scan_mode=scan_mode,
                date_from=date_from_dt,
                date_to=date_to_dt,
            )
            events = await list_scan_alert_events_by_user(
                session,
                user_id,
                limit=limit,
                offset=offset,
                url=url,
                scan_type=scan_type,
                scan_mode=scan_mode,
                date_from=date_from_dt,
                date_to=date_to_dt,
            )
            total_pages = max((total + limit - 1) // limit, 1) if total > 0 else 0
            return ScanAlertHistoryListResponse(
                items=[
                    ScanAlertEventResponse(
                        id=str(e.id),
                        url=e.url,
                        scan_type=getattr(e, "scan_type", "frontend"),
                        scan_mode=getattr(e, "scan_mode", "passive"),
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Supprime un événement d'alerte de l'historique."""
    try:
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Supprime un scan planifié."""
    try:
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
