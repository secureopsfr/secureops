"""Endpoints liés aux préférences utilisateur (thème, langue)."""

import logging
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.schemas.user import LanguagePreferenceResponse, LanguagePreferenceUpdateRequest, ThemePreferenceResponse, ThemePreferenceUpdateRequest
from app.services.user_repository import update_user_dark_mode, update_user_language
from app.utils.auth import require_jwt_user, resolve_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – préférences"])


@router.patch("/preferences/theme", response_model=ThemePreferenceResponse)
async def update_theme_preference(
    theme_data: ThemePreferenceUpdateRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> ThemePreferenceResponse:
    """Met à jour la préférence de thème (dark/light mode)."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            updated_user = await update_user_dark_mode(session, user, theme_data.dark_mode)

            return ThemePreferenceResponse(success=True, dark_mode=updated_user.dark_mode)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la mise à jour de la préférence de thème: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la préférence de thème",
        )


@router.patch("/preferences/language", response_model=LanguagePreferenceResponse)
async def update_language_preference(
    language_data: LanguagePreferenceUpdateRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> LanguagePreferenceResponse:
    """Met à jour la préférence de langue."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            updated_user = await update_user_language(session, user, language_data.language.value)

            return LanguagePreferenceResponse(success=True, language=updated_user.language)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la mise à jour de la préférence de langue: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la préférence de langue",
        )
