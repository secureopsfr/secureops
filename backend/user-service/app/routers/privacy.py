"""Endpoints liés à la vie privée (export des données personnelles)."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.services.scan_alert_repository import list_scan_alert_events_by_user
from app.services.scan_repository import list_scans_by_user_id
from app.services.scheduled_scan_repository import list_scheduled_scans_by_user
from app.services.subscription_repository import get_subscription_by_user_id
from app.services.user_repository import get_user_by_cognito_sub
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – vie privée"])


def _format_scans_section(scans_data: List[dict]) -> List[str]:
    """Formate la section historique des scans pour l'export TXT."""
    lines = ["Historique des scans:"]
    if scans_data:
        for index, scan in enumerate(scans_data, start=1):
            lines.extend(
                [
                    f"  Scan {index}:",
                    f"    url: {scan['url']}",
                    f"    status: {scan['status']}",
                    f"    score: {scan.get('score') or 'N/A'}",
                    f"    timestamp: {scan.get('timestamp') or 'N/A'}",
                    f"    duration: {scan.get('duration') or 'N/A'}",
                    f"    created_at: {scan.get('created_at') or 'N/A'}",
                ]
            )
    else:
        lines.append("  Aucun scan enregistré.")
    return lines


def _format_scheduled_scans_section(scheduled_scans_data: List[dict]) -> List[str]:
    """Formate la section scans planifiés pour l'export TXT."""
    lines = ["Scans planifiés:"]
    if scheduled_scans_data:
        for index, s in enumerate(scheduled_scans_data, start=1):
            lines.extend(
                [
                    f"  Scan planifié {index}:",
                    f"    url: {s['url']}",
                    f"    frequency: {s['frequency']}",
                    f"    schedule_hour: {s['schedule_hour']}",
                    f"    schedule_minute: {s['schedule_minute']}",
                    f"    schedule_day_of_week: {s.get('schedule_day_of_week') or 'N/A'}",
                    f"    schedule_day_of_month: {s.get('schedule_day_of_month') or 'N/A'}",
                    f"    timezone: {s.get('timezone') or 'N/A'}",
                    f"    next_run_at: {s.get('next_run_at') or 'N/A'}",
                    f"    enabled: {s['enabled']}",
                    f"    scan_alerts_enabled: {s['scan_alerts_enabled']}",
                    f"    created_at: {s.get('created_at') or 'N/A'}",
                ]
            )
    else:
        lines.append("  Aucun scan planifié.")
    return lines


def _format_alert_events_section(alert_events_data: List[dict]) -> List[str]:
    """Formate la section historique des alertes pour l'export TXT."""
    lines = ["Historique des alertes:"]
    if alert_events_data:
        for index, e in enumerate(alert_events_data, start=1):
            lines.extend(
                [
                    f"  Alerte {index}:",
                    f"    url: {e['url']}",
                    f"    alert_type: {e['alert_type']}",
                    f"    email_sent: {e['email_sent']}",
                    f"    triggered_at: {e.get('triggered_at') or 'N/A'}",
                ]
            )
    else:
        lines.append("  Aucune alerte enregistrée.")
    return lines


async def _build_export_content(session: AsyncSession, user) -> str:
    """Construit le contenu TXT complet de l'export des données utilisateur."""
    profile_data = {
        "email": user.email,
        "dark_mode": user.dark_mode if user.dark_mode is not None else True,
        "language": user.language if user.language else "fr",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    subscription = await get_subscription_by_user_id(session, user.id)
    subscription_data = (
        {
            "plan": subscription.plan,
            "status": subscription.status,
            "newsletter_enabled": subscription.newsletter_enabled,
            "new_features_notifications_enabled": subscription.new_features_notifications_enabled,
            "history_retention": subscription.history_retention or "30",
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        }
        if subscription
        else {
            "plan": "free",
            "status": "active",
            "newsletter_enabled": False,
            "new_features_notifications_enabled": False,
            "history_retention": "30",
            "created_at": None,
            "updated_at": None,
            "current_period_end": None,
        }
    )

    scans = await list_scans_by_user_id(session, user.id, limit=1000, offset=0)
    scans_data = [
        {
            "url": s.url,
            "status": s.status,
            "score": s.score,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "duration": s.duration,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in scans
    ]

    scheduled_scans = await list_scheduled_scans_by_user(session, user.id, limit=1000, offset=0)
    scheduled_scans_data = [
        {
            "url": s.url,
            "frequency": s.frequency,
            "schedule_hour": s.schedule_hour,
            "schedule_minute": s.schedule_minute,
            "schedule_day_of_week": s.schedule_day_of_week,
            "schedule_day_of_month": s.schedule_day_of_month,
            "timezone": s.timezone,
            "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            "enabled": s.enabled,
            "scan_alerts_enabled": getattr(s, "scan_alerts_enabled", True),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in scheduled_scans
    ]

    alert_events = await list_scan_alert_events_by_user(session, user.id, limit=1000, offset=0)
    alert_events_data = [
        {
            "url": e.url,
            "alert_type": e.alert_type,
            "email_sent": e.email_sent,
            "triggered_at": e.triggered_at.isoformat() if e.triggered_at else None,
        }
        for e in alert_events
    ]

    export_date = datetime.now(UTC).isoformat()
    lines = [
        "Profil:",
        f"  email: {profile_data['email']}",
        f"  dark_mode: {profile_data['dark_mode']}",
        f"  language: {profile_data['language']}",
        f"  created_at: {profile_data.get('created_at') or 'N/A'}",
        "",
        "Abonnement:",
        f"  plan: {subscription_data['plan']}",
        f"  status: {subscription_data['status']}",
        f"  newsletter_enabled: {subscription_data['newsletter_enabled']}",
        f"  new_features_notifications_enabled: {subscription_data['new_features_notifications_enabled']}",
        f"  history_retention: {subscription_data.get('history_retention') or '30'}",
        f"  created_at: {subscription_data.get('created_at') or 'N/A'}",
        f"  updated_at: {subscription_data.get('updated_at') or 'N/A'}",
        f"  current_period_end: {subscription_data.get('current_period_end') or 'N/A'}",
        "",
        *_format_scans_section(scans_data),
        "",
        *_format_scheduled_scans_section(scheduled_scans_data),
        "",
        *_format_alert_events_section(alert_events_data),
        "",
        f"Date d'export: {export_date}",
    ]
    return "\n".join(lines)


@router.get("/export", response_class=PlainTextResponse)
async def export_user_data(
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> PlainTextResponse:
    """Exporte toutes les données personnelles de l'utilisateur (RGPD)."""
    try:
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

            content = await _build_export_content(session, user)
            return PlainTextResponse(content=content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de l'export des données utilisateur: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'export des données",
        )
