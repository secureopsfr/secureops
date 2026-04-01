"""API utilisateur : vérification DNS des domaines (modes non passifs)."""

from __future__ import annotations

import logging
from typing import Annotated, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response

from app.db import get_async_session
from app.schemas.domain_verification import (
    DomainVerificationChallengeCreateRequest,
    DomainVerificationChallengeResponse,
    DomainVerificationItem,
    DomainVerificationVerifyRequest,
)
from app.services import domain_verification_repository as repo
from app.services.domain_verification_service import (
    create_challenge,
    delete_verification_for_user,
    normalize_domain_from_user_input,
    txt_fqdn_for_domain,
    verify_challenge,
)
from app.services.user_repository import get_user_by_cognito_sub
from app.utils.auth import require_jwt_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user/domain-verifications", tags=["user – domain verifications"])


@router.post("/challenges", response_model=DomainVerificationChallengeResponse)
async def post_challenge(
    body: DomainVerificationChallengeCreateRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> DomainVerificationChallengeResponse:
    """Crée un challenge et retourne le token TXT à publier."""
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="missing_sub")
    async with get_async_session() as session:
        domain, token, exp, already = await create_challenge(session, cognito_sub=str(cognito_sub), raw_input=body.url)
        await session.commit()
    if already:
        return DomainVerificationChallengeResponse(
            domain=domain,
            txt_name=txt_fqdn_for_domain(domain),
            txt_value="",
            challenge_expires_at=exp,
            already_verified=True,
        )
    return DomainVerificationChallengeResponse(
        domain=domain,
        txt_name=txt_fqdn_for_domain(domain),
        txt_value=token,
        challenge_expires_at=exp,
        already_verified=False,
    )


@router.post(
    "/verify",
    status_code=204,
    response_class=Response,
)
async def post_verify(
    body: DomainVerificationVerifyRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> Response:
    """Vérifie le TXT DNS et enregistre le domaine."""
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="missing_sub")
    domain = normalize_domain_from_user_input(body.domain)
    async with get_async_session() as session:
        await verify_challenge(session, cognito_sub=str(cognito_sub), domain=domain)
    return Response(status_code=204)


@router.get("", response_model=list[DomainVerificationItem])
async def list_verifications(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> list[DomainVerificationItem]:
    """Liste les domaines vérifiés et encore valides."""
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="missing_sub")
    async with get_async_session() as session:
        user = await get_user_by_cognito_sub(session, str(cognito_sub))
        if not user:
            raise HTTPException(status_code=404, detail="user_not_found")
        rows = await repo.list_verifications_for_user(session, user.id, active_only=True)
    return [DomainVerificationItem(id=r.id, domain=r.domain, verified_at=r.verified_at, expires_at=r.expires_at) for r in rows]


@router.delete(
    "/{verification_id}",
    status_code=204,
    response_class=Response,
)
async def delete_verification_route(
    verification_id: UUID,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> Response:
    """Retire la confiance côté produit pour un domaine vérifié."""
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="missing_sub")
    async with get_async_session() as session:
        await delete_verification_for_user(session, cognito_sub=str(cognito_sub), verification_id=verification_id)
    return Response(status_code=204)
