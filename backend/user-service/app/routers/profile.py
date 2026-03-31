"""Endpoints liés au profil utilisateur (init, me, update)."""

import logging
from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.db import get_async_session
from app.schemas.user import ProfileUpdateRequest, ProfileUpdateResponse
from app.services.user_repository import get_or_create_user, get_user_by_cognito_sub
from app.services.user_service import update_user_profile
from app.utils.auth import require_jwt_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – profil"])


class InitUserRequest(BaseModel):
    """Payload optionnel pour /init (ex. email quand Cognito admin indisponible)."""

    email: Optional[str] = None


_DEFAULT_INIT_USER_BODY = InitUserRequest()


@router.post("/init")
async def init_user(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
    body: InitUserRequest = _DEFAULT_INIT_USER_BODY,
) -> Dict:
    """Initialise l'utilisateur en base de données (lazy creation).

    Doit être appelé après la connexion pour créer l'utilisateur
    en base de données s'il n'existe pas encore. L'email peut être
    fourni dans le body (extrait de l'ID token côté frontend) pour
    les environnements dev sans accès à l'API Cognito admin.
    """
    dark_mode = True
    language = "fr"
    is_new_user = False
    try:
        cognito_sub = current_user.get("sub")
        if cognito_sub:
            async with get_async_session() as session:
                user = await get_user_by_cognito_sub(session, cognito_sub)
                if not user and body.email:
                    # Fallback: create user directly with email from request body
                    logger.info(
                        "Création directe de l'utilisateur via email du body: sub=%s",
                        cognito_sub,
                    )
                    user, is_new_user = await get_or_create_user(session, cognito_sub, body.email)
                if user:
                    dark_mode = user.dark_mode if user.dark_mode is not None else True
                    language = user.language if user.language else "fr"
    except Exception as e:
        logger.warning("Impossible de récupérer/créer l'utilisateur: %s", e)

    return {
        "success": True,
        "sub": current_user.get("sub"),
        "username": current_user.get("username"),
        "email": current_user.get("email") or body.email,
        "groups": current_user.get("cognito:groups", []),
        "is_new_user": current_user.get("is_new_user", False) or is_new_user,
        "dark_mode": dark_mode,
        "language": language,
    }


@router.get("/me")
async def get_current_user_info(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> Dict:
    """Retourne les informations de l'utilisateur actuel."""
    dark_mode = True
    language = "fr"
    try:
        cognito_sub = current_user.get("sub")
        if cognito_sub:
            async with get_async_session() as session:
                user = await get_user_by_cognito_sub(session, cognito_sub)
                if user:
                    dark_mode = user.dark_mode if user.dark_mode is not None else True
                    language = user.language if user.language else "fr"
    except Exception as e:
        logger.warning("Impossible de récupérer les préférences utilisateur: %s", e)

    return {
        "sub": current_user.get("sub"),
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "groups": current_user.get("cognito:groups", []),
        "dark_mode": dark_mode,
        "language": language,
    }


@router.put("/profile", response_model=ProfileUpdateResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> ProfileUpdateResponse:
    """Met à jour le profil de l'utilisateur (prénom, nom)."""
    logger.info("=== PUT /api/user/profile appelé ===")
    logger.info("Données reçues: given_name=%s, family_name=%s", profile_data.given_name, profile_data.family_name)
    logger.info("Utilisateur authentifié: %s", current_user.get("sub"))
    try:
        result = update_user_profile(
            user_claims=current_user,
            given_name=profile_data.given_name,
            family_name=profile_data.family_name,
        )
        return ProfileUpdateResponse(success=result.success, message=result.message)

    except ValueError as e:
        logger.error("Erreur de validation lors de la mise à jour du profil: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Erreur lors de la mise à jour du profil: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du profil",
        )
