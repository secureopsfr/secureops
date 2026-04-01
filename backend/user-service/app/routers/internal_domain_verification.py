"""Endpoint interne : contrôle domaine vérifié (scan-service, scheduler)."""

import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException

from app.db import get_async_session
from app.schemas.domain_verification import DomainVerificationAssertRequest, DomainVerificationAssertResponse
from app.services.domain_verification_service import assert_domain_allowed

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("USER_SERVICE_INTERNAL_API_KEY")
_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")

router = APIRouter(prefix="/api/internal/domain-verifications", tags=["internal – domain verifications"])


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    if not INTERNAL_API_KEY:
        raise HTTPException(status_code=503, detail="internal_api_key_not_configured")
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="invalid_internal_api_key")


_VERIFY = Depends(_verify_internal_api_key)


@router.post("/assert", response_model=DomainVerificationAssertResponse)
async def post_assert(
    body: DomainVerificationAssertRequest,
    _: None = _VERIFY,
) -> DomainVerificationAssertResponse:
    """Indique si l'utilisateur (cognito_sub) a une vérification DNS active pour le domaine (eTLD+1)."""
    async with get_async_session() as session:
        allowed, reason = await assert_domain_allowed(session, cognito_sub=body.cognito_sub, domain=body.domain)
    return DomainVerificationAssertResponse(allowed=allowed, reason=reason)
