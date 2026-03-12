"""Endpoints liés à la sécurité du compte (mot de passe, suppression, déconnexion)."""

import logging
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.exceptions import CognitoConfigurationError, InvalidPasswordError
from app.schemas.user import ChangePasswordRequest, ChangePasswordResponse
from app.services.cognito_service import delete_user as delete_cognito_user
from app.services.cognito_service import revoke_all_user_tokens
from app.services.user_repository import delete_user_by_id
from app.services.user_service import change_user_password_service
from app.utils.auth import require_jwt_user, resolve_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – sécurité"])


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> ChangePasswordResponse:
    """Change le mot de passe de l'utilisateur."""
    try:
        result = change_user_password_service(
            user_claims=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        return ChangePasswordResponse(success=result.success, message=result.message)

    except InvalidPasswordError as e:
        logger.error("Mot de passe incorrect: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except CognitoConfigurationError as e:
        logger.error("Configuration Cognito incomplète: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ValueError as e:
        logger.error("Erreur de validation lors du changement de mot de passe: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Erreur lors du changement de mot de passe: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du changement de mot de passe",
        )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> None:
    """Supprime le compte de l'utilisateur (Cognito + BDD)."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            user_id = user.id
            cognito_sub = current_user.get("sub")
            username = current_user.get("username") or cognito_sub

            # Supprimer dans Cognito
            try:
                delete_cognito_user(username)
            except Exception as cognito_err:
                logger.error("Erreur lors de la suppression dans Cognito (continuation): %s", cognito_err, exc_info=True)

            # Supprimer en BDD (cascade : favoris + abonnement)
            deleted = await delete_user_by_id(session, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé en base de données",
                )

            logger.info("Compte utilisateur supprimé: user_id=%s, cognito_sub=%s", user_id, cognito_sub)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression du compte: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du compte",
        )


@router.post("/logout-all-devices", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_devices(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> None:
    """Révoque tous les tokens, déconnectant tous les appareils."""
    try:
        username = current_user.get("username")
        cognito_sub = current_user.get("sub")

        if not username:
            username = cognito_sub
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossible d'identifier l'utilisateur",
            )

        try:
            revoke_all_user_tokens(username)
            logger.info("Tous les tokens révoqués pour l'utilisateur: username=%s, sub=%s", username, cognito_sub)
        except Exception as e:
            logger.error("Erreur lors de la révocation des tokens: %s", e, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la déconnexion de tous les appareils",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la déconnexion de tous les appareils: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion de tous les appareils",
        )
