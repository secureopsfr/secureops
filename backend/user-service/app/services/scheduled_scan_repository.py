"""Repository pour la gestion des scans planifiés en base de données."""

import logging
import uuid
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_scan import ScheduledScan
from app.utils.query_utils import apply_scan_mode_filter, apply_scan_type_filter, apply_url_filter

logger = logging.getLogger(__name__)


def _apply_optional_scheduled_scan_fields(scan: ScheduledScan, fields: dict[str, object]) -> None:
    """Assigne sur `scan` uniquement les entrées dont la valeur n'est pas None."""
    for attr, value in fields.items():
        if value is not None:
            setattr(scan, attr, value)


async def create_scheduled_scan(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: str,
    scan_type: str,
    frequency: str,
    scan_mode: str = "passive",
    result_mode: str = "single",
    urls: Optional[List[str]] = None,
    schedule_hour: int = 2,
    schedule_minute: int = 0,
    schedule_day_of_week: Optional[int] = None,
    schedule_day_of_month: Optional[int] = None,
    timezone_name: Optional[str] = None,
    scan_alerts_enabled: bool = True,
    alert_on_regression: bool = True,
    alert_on_critical_finding: bool = True,
    alert_score_threshold: Optional[int] = None,
) -> ScheduledScan:
    """Crée un scan planifié.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        url: URL à scanner.
        result_mode: Mode de résultat (single ou multi).
        urls: Liste d'URLs pour un scan multi-pages.
        frequency: daily, weekly ou monthly.
        schedule_hour: Heure d'exécution (dans le fuseau utilisateur).
        schedule_minute: Minute d'exécution.
        schedule_day_of_week: Jour de la semaine (weekly).
        schedule_day_of_month: Jour du mois (monthly).
        timezone_name: Fuseau utilisateur (ex. Europe/Paris). Si null, UTC.

    Returns:
        ScheduledScan: Le scan planifié créé.
    """
    from app.services.scheduled_scan_utils import compute_initial_next_run

    next_run_at = compute_initial_next_run(
        frequency=frequency,
        schedule_hour=schedule_hour,
        schedule_minute=schedule_minute,
        schedule_day_of_week=schedule_day_of_week,
        schedule_day_of_month=schedule_day_of_month,
        timezone_name=timezone_name,
    )
    scan = ScheduledScan(
        user_id=user_id,
        url=url,
        scan_type=scan_type,
        scan_mode=scan_mode,
        result_mode=result_mode,
        urls_json=urls,
        frequency=frequency,
        schedule_hour=schedule_hour,
        schedule_minute=schedule_minute,
        schedule_day_of_week=schedule_day_of_week,
        schedule_day_of_month=schedule_day_of_month,
        timezone=timezone_name,
        next_run_at=next_run_at,
        enabled=True,
        scan_alerts_enabled=scan_alerts_enabled,
        alert_on_regression=alert_on_regression,
        alert_on_critical_finding=alert_on_critical_finding,
        alert_score_threshold=alert_score_threshold,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    logger.info("Scan planifié créé: id=%s, user_id=%s, url=%s", scan.id, user_id, url[:50])
    return scan


async def get_scheduled_scan_by_id(
    session: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[ScheduledScan]:
    """Récupère un scan planifié par ID si il appartient à l'utilisateur.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan planifié.
        user_id: UUID de l'utilisateur (vérification propriété).

    Returns:
        ScheduledScan ou None si non trouvé.
    """
    result = await session.execute(select(ScheduledScan).where(ScheduledScan.id == scan_id, ScheduledScan.user_id == user_id))
    return result.scalar_one_or_none()


async def count_scheduled_scans_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
    scan_mode: Optional[str] = None,
) -> int:
    """Compte le nombre total de scans planifiés d'un utilisateur.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        url: Filtre optionnel par URL exacte.

    Returns:
        Nombre total de scans planifiés.
    """
    stmt = select(func.count(ScheduledScan.id)).where(ScheduledScan.user_id == user_id)
    stmt = apply_url_filter(stmt, ScheduledScan.url, url)
    stmt = apply_scan_type_filter(stmt, ScheduledScan.scan_type, scan_type)
    stmt = apply_scan_mode_filter(stmt, ScheduledScan.scan_mode, scan_mode)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def list_scheduled_scans_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
    scan_mode: Optional[str] = None,
) -> List[ScheduledScan]:
    """Liste les scans planifiés d'un utilisateur (pagination).

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.
        limit: Nombre max d'éléments.
        offset: Décalage pour pagination.
        url: Filtre optionnel par URL exacte.
        scan_type: Filtre optionnel (frontend, backend, both).

    Returns:
        Liste des scans planifiés.
    """
    stmt = select(ScheduledScan).where(ScheduledScan.user_id == user_id)
    stmt = apply_url_filter(stmt, ScheduledScan.url, url)
    stmt = apply_scan_type_filter(stmt, ScheduledScan.scan_type, scan_type)
    stmt = apply_scan_mode_filter(stmt, ScheduledScan.scan_mode, scan_mode)
    stmt = stmt.order_by(ScheduledScan.next_run_at).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_scans_due_for_execution(
    session: AsyncSession,
    before: Optional[datetime] = None,
) -> List[ScheduledScan]:
    """Récupère les scans planifiés à exécuter (next_run_at <= before, enabled).

    Args:
        session: Session de base de données.
        before: Date limite (défaut : maintenant UTC).

    Returns:
        Liste des scans à exécuter.
    """
    if before is None:
        before = datetime.now(UTC)
    result = await session.execute(
        select(ScheduledScan).where(ScheduledScan.enabled.is_(True), ScheduledScan.next_run_at <= before).order_by(ScheduledScan.next_run_at)
    )
    return list(result.scalars().all())


async def update_scheduled_scan(
    session: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    frequency: Optional[str] = None,
    schedule_hour: Optional[int] = None,
    schedule_minute: Optional[int] = None,
    schedule_day_of_week: Optional[int] = None,
    schedule_day_of_month: Optional[int] = None,
    timezone_name: Optional[str] = None,
    enabled: Optional[bool] = None,
    scan_alerts_enabled: Optional[bool] = None,
    alert_on_regression: Optional[bool] = None,
    alert_on_critical_finding: Optional[bool] = None,
    alert_score_threshold: Optional[int] = None,
) -> Optional[ScheduledScan]:
    """Met à jour un scan planifié.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan.
        user_id: UUID de l'utilisateur (vérification propriété).
        frequency: Nouvelle fréquence.
        schedule_hour: Nouvelle heure.
        schedule_minute: Nouvelle minute.
        schedule_day_of_week: Nouveau jour de semaine.
        schedule_day_of_month: Nouveau jour du mois.
        enabled: Actif ou en pause.

    Returns:
        ScheduledScan mis à jour ou None si non trouvé.
    """
    scan = await get_scheduled_scan_by_id(session, scan_id, user_id)
    if not scan:
        return None

    _apply_optional_scheduled_scan_fields(
        scan,
        {
            "frequency": frequency,
            "schedule_hour": schedule_hour,
            "schedule_minute": schedule_minute,
            "schedule_day_of_week": schedule_day_of_week,
            "schedule_day_of_month": schedule_day_of_month,
            "timezone": timezone_name,
            "enabled": enabled,
            "scan_alerts_enabled": scan_alerts_enabled,
            "alert_on_regression": alert_on_regression,
            "alert_on_critical_finding": alert_on_critical_finding,
            "alert_score_threshold": alert_score_threshold,
        },
    )

    scan.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(scan)
    return scan


async def update_next_run_at(
    session: AsyncSession,
    scan_id: uuid.UUID,
    next_run_at: datetime,
) -> bool:
    """Met à jour next_run_at après une exécution réussie.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan planifié.
        next_run_at: Nouvelle date de prochaine exécution.

    Returns:
        True si mis à jour, False si scan non trouvé.
    """
    result = await session.execute(select(ScheduledScan).where(ScheduledScan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        return False
    scan.next_run_at = next_run_at
    scan.updated_at = datetime.now(UTC)
    await session.commit()
    logger.info("next_run_at mis à jour pour scheduled_scan %s: %s", scan_id, next_run_at)
    return True


async def delete_scheduled_scan(
    session: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Supprime un scan planifié.

    Args:
        session: Session de base de données.
        scan_id: UUID du scan.
        user_id: UUID de l'utilisateur (vérification propriété).

    Returns:
        True si supprimé, False sinon.
    """
    scan = await get_scheduled_scan_by_id(session, scan_id, user_id)
    if not scan:
        return False
    await session.delete(scan)
    await session.commit()
    logger.info("Scan planifié supprimé: id=%s, user_id=%s", scan_id, user_id)
    return True
