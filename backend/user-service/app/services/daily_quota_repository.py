"""Repository pour la gestion des quotas journaliers (scans + crawls cumulés)."""

import logging
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config_loader import settings
from app.models.daily_quota import DailyQuota

logger = logging.getLogger(__name__)


def _default_limit() -> int:
    """Retourne la limite de quota depuis la configuration."""
    return settings().daily_quota.limit


def today_utc() -> date:
    """Retourne la date courante en UTC."""
    return datetime.now(UTC).date()


def next_midnight_utc() -> datetime:
    """Retourne le prochain minuit UTC (reset du quota)."""
    d = datetime.now(UTC).date()
    return datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)


async def get_today_used(session: AsyncSession, *, cognito_sub: str) -> int:
    """Retourne le nombre de jobs utilisés aujourd'hui pour cet utilisateur."""
    result = await session.execute(
        select(DailyQuota.jobs_count).where(
            DailyQuota.cognito_sub == cognito_sub,
            DailyQuota.date_utc == today_utc(),
        )
    )
    return result.scalar_one_or_none() or 0


async def check_and_increment_quota(
    session: AsyncSession,
    *,
    cognito_sub: str,
    limit: int | None = None,
) -> tuple[bool, int]:
    """Vérifie et incrémente le quota journalier de façon atomique.

    Utilise INSERT ON CONFLICT DO NOTHING pour créer la ligne si elle
    n'existe pas, puis SELECT FOR UPDATE pour verrouiller et incrémenter
    sans race condition.

    Returns:
        (allowed, remaining) — allowed=False si le quota est dépassé.
    """
    if limit is None:
        limit = _default_limit()
    today = today_utc()

    # S'assurer que la ligne existe (INSERT … ON CONFLICT DO NOTHING)
    upsert = (
        pg_insert(DailyQuota)
        .values(
            id=uuid.uuid4(),
            cognito_sub=cognito_sub,
            date_utc=today,
            jobs_count=0,
            created_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(constraint="uq_daily_quotas_sub_date")
    )
    await session.execute(upsert)
    await session.flush()

    # Verrouiller la ligne pour éviter les increments concurrents
    result = await session.execute(select(DailyQuota).where(DailyQuota.cognito_sub == cognito_sub, DailyQuota.date_utc == today).with_for_update())
    row = result.scalar_one_or_none()

    if row is None:
        logger.error("Ligne daily_quota introuvable après upsert pour sub=%s", cognito_sub)
        return False, 0

    if row.jobs_count >= limit:
        return False, 0

    row.jobs_count += 1
    await session.flush()
    return True, limit - row.jobs_count
