"""Endpoint interne de vérification/incrément quota journalier (appelé par la gateway)."""

import logging
import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.config_loader import settings
from app.db import get_async_session
from app.services.daily_quota_repository import check_and_increment_quota

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("USER_SERVICE_INTERNAL_API_KEY")
_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")

router = APIRouter(prefix="/api/internal/quota", tags=["internal – quota"])


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie strictement la clé API interne (même pattern que internal_api_keys)."""
    if not INTERNAL_API_KEY:
        raise HTTPException(status_code=503, detail="Clé API interne non configurée")
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY = Depends(_verify_internal_api_key)


def _next_midnight_utc_iso() -> str:
    d = datetime.now(UTC).date()
    return (datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)).isoformat()


class QuotaCheckRequest(BaseModel):
    """Corps de requête pour la vérification/incrément du quota."""

    cognito_sub: str = Field(..., min_length=1, description="Identifiant Cognito de l'utilisateur")
    limit: int = Field(default_factory=lambda: settings().daily_quota.limit, ge=1, description="Limite journalière")


class QuotaCheckResponse(BaseModel):
    """Réponse du check quota."""

    allowed: bool
    remaining: int
    reset_at: str


@router.post("/check-and-increment", response_model=QuotaCheckResponse)
async def check_and_increment(
    body: QuotaCheckRequest,
    _: None = _VERIFY,
) -> QuotaCheckResponse:
    """Vérifie et incrémente le quota journalier de l'utilisateur.

    Opération atomique : si le quota est disponible, l'incrément est
    immédiatement comptabilisé et committed. Appelé par la gateway
    avant de proxifier POST /scan/async et POST /crawl/async.
    """
    async with get_async_session() as session:
        allowed, remaining = await check_and_increment_quota(
            session,
            cognito_sub=body.cognito_sub,
            limit=body.limit,
        )
        if allowed:
            await session.commit()
        return QuotaCheckResponse(
            allowed=allowed,
            remaining=remaining,
            reset_at=_next_midnight_utc_iso(),
        )
