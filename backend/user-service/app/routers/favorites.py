"""Endpoints CRUD pour les favoris de recherche."""

import logging
import uuid
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.schemas.favorite import FavoriteCreateRequest, FavoriteListResponse, FavoriteResponse
from app.services.favorite_repository import (
    count_user_favorites,
    create_or_update_favorite,
    delete_favorite_by_id,
    delete_user_favorites,
    get_user_favorites,
)
from app.utils.auth import get_current_user, resolve_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – favoris"])


@router.post("/favorites", response_model=FavoriteResponse)
async def create_favorite_entry(
    favorite_data: FavoriteCreateRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> FavoriteResponse:
    """Crée une nouvelle entrée de favori."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            favorite = await create_or_update_favorite(
                session=session,
                user_id=user.id,
                search_type=favorite_data.search_type,
                query_json=favorite_data.query_json,
            )

            return FavoriteResponse(
                id=str(favorite.id),
                user_id=str(favorite.user_id),
                search_type=favorite.search_type,
                query_json=favorite.query_json,
                created_at=favorite.created_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la création du favori: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du favori",
        )


@router.get("/favorites", response_model=FavoriteListResponse)
async def get_favorites(
    current_user: Annotated[Dict, Depends(get_current_user)],
    limit: int = 20,
    offset: int = 0,
) -> FavoriteListResponse:
    """Récupère les favoris avec pagination."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            total = await count_user_favorites(session, user.id)
            favorites = await get_user_favorites(session, user.id, limit=limit, offset=offset)

            per_page = max(limit, 1)
            page = (offset // per_page) + 1
            total_pages = max((total + per_page - 1) // per_page, 1) if total > 0 else 0

            return FavoriteListResponse(
                items=[
                    FavoriteResponse(
                        id=str(f.id),
                        user_id=str(f.user_id),
                        search_type=f.search_type,
                        query_json=f.query_json,
                        created_at=f.created_at,
                    )
                    for f in favorites
                ],
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération des favoris: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des favoris",
        )


@router.delete("/favorites/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    favorite_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> None:
    """Supprime un favori par son ID."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            try:
                favorite_uuid = uuid.UUID(favorite_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de favori invalide",
                )

            deleted = await delete_favorite_by_id(session, favorite_uuid, user.id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Favori non trouvé ou n'appartient pas à l'utilisateur",
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression du favori: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du favori",
        )


@router.delete("/favorites", status_code=status.HTTP_200_OK)
async def delete_all_favorites(
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> Dict[str, int]:
    """Supprime tous les favoris de l'utilisateur."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            deleted_count = await delete_user_favorites(session, user.id)
            return {"deleted_count": deleted_count}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la suppression des favoris: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression des favoris",
        )
