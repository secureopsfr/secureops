"""Endpoint public pour la consultation du quota journalier (appelé par le frontend)."""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config_loader import settings
from app.db import get_async_session
from app.services.daily_quota_repository import get_today_used
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)


def _quota_limit() -> int:
    """Retourne la limite (settings > env DAILY_QUOTA_LIMIT)."""
    return int(os.getenv("DAILY_QUOTA_LIMIT", str(settings().daily_quota.limit)))


router = APIRouter(prefix="/api/user/quota", tags=["quota"])


def _next_midnight_utc_iso() -> str:
    d = datetime.now(UTC).date()
    return (datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)).isoformat()


class DailyQuotaResponse(BaseModel):
    """Quota journalier de l'utilisateur authentifié."""

    used: int
    remaining: int
    limit: int
    reset_at: str


@router.get("/daily", response_model=DailyQuotaResponse)
async def get_daily_quota(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> DailyQuotaResponse:
    """Retourne la consommation et le quota restant pour aujourd'hui (UTC).

    Le compteur regroupe scans et crawls cumulés.
    Reset quotidien à minuit UTC.
    Appelé par le frontend pour afficher le compteur dans le header.
    """
    cognito_sub: str = current_user["sub"]

    async with get_async_session() as session:
        used = await get_today_used(session, cognito_sub=cognito_sub)

    limit = _quota_limit()
    remaining = max(0, limit - used)
    return DailyQuotaResponse(
        used=used,
        remaining=remaining,
        limit=limit,
        reset_at=_next_midnight_utc_iso(),
    )
