"""Repository pour la gestion des scans (historique) en base de données."""

import logging
import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan

logger = logging.getLogger(__name__)


def _parse_timestamp(ts: str) -> datetime:
    """Parse un timestamp ISO en datetime timezone-aware.

    Args:
        ts: Chaîne ISO (ex. 2026-03-02T12:00:00.000Z).

    Returns:
        datetime: Objet datetime timezone-aware.
    """
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


async def create_scan(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: str,
    status: str,
    score: Optional[int],
    findings: List[dict[str, Any]],
    timestamp: str,
    duration: float,
) -> Scan:
    """Crée un scan dans l'historique.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        url: URL scannée.
        status: Statut (success, error).
        score: Note /100 (nullable).
        findings: Liste des findings (dicts sérialisables).
        timestamp: Horodatage ISO du scan.
        duration: Durée en secondes.

    Returns:
        Scan: Le scan créé.
    """
    scan = Scan(
        user_id=user_id,
        url=url,
        status=status,
        score=score,
        findings_json=findings,
        timestamp=_parse_timestamp(timestamp),
        duration=duration,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    logger.info("Scan créé: id=%s, user_id=%s, url=%s", scan.id, user_id, url[:50])
    return scan


async def get_scan_by_id(session: AsyncSession, scan_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Scan]:
    """Récupère un scan par ID si il appartient à l'utilisateur.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan.
        user_id: UUID de l'utilisateur (vérification propriété).

    Returns:
        Scan ou None si non trouvé ou n'appartient pas à l'utilisateur.
    """
    result = await session.execute(select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id))
    return result.scalar_one_or_none()


async def list_scans_by_user_id(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> List[Scan]:
    """Liste les scans d'un utilisateur (pagination, tri par date décroissante).

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        limit: Nombre max d'éléments.
        offset: Décalage pour pagination.

    Returns:
        Liste des scans.
    """
    result = await session.execute(select(Scan).where(Scan.user_id == user_id).order_by(desc(Scan.created_at)).limit(limit).offset(offset))
    return list(result.scalars().all())


async def count_user_scans(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Compte le nombre total de scans d'un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.

    Returns:
        Nombre total de scans.
    """
    result = await session.execute(select(func.count(Scan.id)).where(Scan.user_id == user_id))
    return result.scalar() or 0


async def delete_scan_by_id(session: AsyncSession, scan_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Supprime un scan par ID si il appartient à l'utilisateur.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan.
        user_id: UUID de l'utilisateur (vérification propriété).

    Returns:
        True si supprimé, False sinon.
    """
    scan = await get_scan_by_id(session, scan_id, user_id)
    if not scan:
        return False
    await session.delete(scan)
    await session.commit()
    logger.info("Scan supprimé: id=%s, user_id=%s", scan_id, user_id)
    return True


async def delete_all_user_scans(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Supprime tous les scans d'un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.

    Returns:
        Nombre de scans supprimés.
    """
    result = await session.execute(select(Scan).where(Scan.user_id == user_id))
    scans = list(result.scalars().all())
    for scan in scans:
        await session.delete(scan)
    await session.commit()
    logger.info("Tous les scans supprimés pour user_id=%s: %s entrées", user_id, len(scans))
    return len(scans)
