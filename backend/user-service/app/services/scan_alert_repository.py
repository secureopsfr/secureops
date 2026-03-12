"""Repository pour l'historique des alertes de scans planifiés."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_alert_event import ScanAlertEvent
from app.utils.query_utils import apply_date_filter, apply_scan_type_filter, apply_url_filter

logger = logging.getLogger(__name__)


async def create_scan_alert_event(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: str,
    scan_type: str,
    alert_type: str,
    email_sent: bool,
    scheduled_scan_id: uuid.UUID | None = None,
) -> ScanAlertEvent:
    """Enregistre un événement d'alerte déclenché.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        url: URL scannée.
        alert_type: regression ou critical_finding.
        email_sent: True si l'email a été envoyé avec succès.
        scheduled_scan_id: UUID du scan planifié (optionnel).

    Returns:
        ScanAlertEvent: L'événement créé.
    """
    event = ScanAlertEvent(
        user_id=user_id,
        scheduled_scan_id=scheduled_scan_id,
        url=url,
        scan_type=scan_type,
        alert_type=alert_type,
        email_sent=email_sent,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def count_scan_alert_events_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> int:
    """Compte le nombre total d'événements d'alerte d'un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        url: Filtre optionnel par URL exacte.
        scan_type: Filtre optionnel (frontend, backend, custom).
        date_from: Filtre optionnel date de début (triggered_at).
        date_to: Filtre optionnel date de fin (triggered_at).

    Returns:
        Nombre total d'événements.
    """
    stmt = select(func.count(ScanAlertEvent.id)).where(ScanAlertEvent.user_id == user_id)
    stmt = apply_url_filter(stmt, ScanAlertEvent.url, url)
    stmt = apply_scan_type_filter(stmt, ScanAlertEvent.scan_type, scan_type)
    stmt = apply_date_filter(stmt, ScanAlertEvent.triggered_at, date_from, date_to)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def list_scan_alert_events_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[ScanAlertEvent]:
    """Liste les événements d'alerte d'un utilisateur (pagination, du plus récent au plus ancien).

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        limit: Nombre max d'éléments.
        offset: Décalage pour pagination.
        url: Filtre optionnel par URL exacte.
        scan_type: Filtre optionnel (frontend, backend, custom).
        date_from: Filtre optionnel date de début (triggered_at).
        date_to: Filtre optionnel date de fin (triggered_at).

    Returns:
        Liste des ScanAlertEvent.
    """
    stmt = select(ScanAlertEvent).where(ScanAlertEvent.user_id == user_id)
    stmt = apply_url_filter(stmt, ScanAlertEvent.url, url)
    stmt = apply_scan_type_filter(stmt, ScanAlertEvent.scan_type, scan_type)
    stmt = apply_date_filter(stmt, ScanAlertEvent.triggered_at, date_from, date_to)
    stmt = stmt.order_by(ScanAlertEvent.triggered_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_scan_alert_event(
    session: AsyncSession,
    event_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Supprime un événement d'alerte s'il appartient à l'utilisateur.

    Args:
        session: Session de base de données.
        event_id: UUID de l'événement.
        user_id: UUID de l'utilisateur (vérification propriété).

    Returns:
        True si supprimé, False si non trouvé.
    """
    result = await session.execute(
        delete(ScanAlertEvent).where(ScanAlertEvent.id == event_id, ScanAlertEvent.user_id == user_id),
    )
    await session.commit()
    return result.rowcount > 0


async def delete_all_alert_events_by_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Supprime tous les événements d'alerte d'un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.

    Returns:
        Nombre d'événements supprimés.
    """
    result = await session.execute(delete(ScanAlertEvent).where(ScanAlertEvent.user_id == user_id))
    deleted = result.rowcount or 0
    await session.commit()
    if deleted > 0:
        logger.info("Toutes les alertes supprimées pour user_id=%s: %s entrées", user_id, deleted)
    return deleted


async def delete_alert_events_older_than_days(
    session: AsyncSession,
    user_id: uuid.UUID,
    days: int,
) -> int:
    """Supprime les événements d'alerte plus anciens que X jours pour un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        days: Nombre de jours (ex. 7, 30, 90).

    Returns:
        Nombre d'événements supprimés.
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = await session.execute(
        delete(ScanAlertEvent).where(ScanAlertEvent.user_id == user_id, ScanAlertEvent.triggered_at < cutoff),
    )
    deleted = result.rowcount or 0
    await session.commit()
    if deleted > 0:
        logger.info("Alertes supprimées pour user_id=%s (plus vieilles que %s jours): %s entrées", user_id, days, deleted)
    return deleted
