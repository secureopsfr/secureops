"""Endpoint interne pour la vérification des clés API (appelé par le gateway)."""

import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_async_session
from app.services.api_key_repository import get_api_key_by_plain_key, update_last_used_at

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("USER_SERVICE_INTERNAL_API_KEY")
_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie la clé API interne si USER_SERVICE_INTERNAL_API_KEY est définie."""
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY_INTERNAL_API_KEY = Depends(_verify_internal_api_key)


class VerifyKeyRequest(BaseModel):
    """Corps de requête pour la vérification d'une clé API."""

    key: str = Field(..., min_length=1, description="Clé API en clair")


class VerifyKeyResponse(BaseModel):
    """Réponse de vérification — infos utilisateur pour le gateway."""

    user_id: str = Field(..., description="UUID de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    sub: str = Field(..., description="Identifiant (cognito_sub) pour compatibilité")


router = APIRouter(prefix="/api/internal/keys", tags=["internal – clés API"])


@router.post("/verify", response_model=VerifyKeyResponse)
async def verify_api_key(
    body: VerifyKeyRequest,
    _: None = _VERIFY_INTERNAL_API_KEY,
) -> VerifyKeyResponse:
    """Vérifie une clé API et retourne les infos utilisateur.

    Appelé par le gateway pour authentifier les requêtes avec X-API-Key.
    Met à jour last_used_at si la clé est valide.
    """
    async with get_async_session() as session:
        api_key = await get_api_key_by_plain_key(session, body.key.strip())
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API invalide ou révoquée",
            )
        if api_key.expires_at and datetime.now(UTC) > api_key.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API expirée",
            )
        await update_last_used_at(session, api_key)
        await session.commit()
        user = api_key.user
        return VerifyKeyResponse(
            user_id=str(user.id),
            email=user.email,
            sub=user.cognito_sub,
        )
