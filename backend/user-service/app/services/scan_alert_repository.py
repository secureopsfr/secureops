"""Repository pour l'historique des alertes de scans planifiés."""

import uuid
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_alert_event import ScanAlertEvent


async def create_scan_alert_event(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: str,
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
        alert_type=alert_type,
        email_sent=email_sent,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def list_scan_alert_events_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 100,
) -> List[ScanAlertEvent]:
    """Liste les événements d'alerte d'un utilisateur, du plus récent au plus ancien.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        limit: Nombre maximum d'événements à retourner.

    Returns:
        Liste des ScanAlertEvent.
    """
    result = await session.execute(
        select(ScanAlertEvent).where(ScanAlertEvent.user_id == user_id).order_by(ScanAlertEvent.triggered_at.desc()).limit(limit),
    )
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
