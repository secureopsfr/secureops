"""Endpoints pour la gestion des clés API (API publique)."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.config_loader import settings
from app.db import get_async_session
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyListItem, ApiKeyListResponse, ApiKeyUpdateRequest
from app.services.api_key_repository import (
    _parse_expires_at,
    count_api_keys_by_user,
    create_api_key,
    delete_api_key,
    exists_api_key_with_name,
    list_api_keys_by_user,
    update_api_key,
)
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keys", tags=["clés API"])


def _resolve_expiry_params(
    expires_at: str | None,
    ttl_days: int | None,
    *,
    require_explicit: bool = False,
) -> tuple:
    """Résout expires_at ou ttl_days en (expires_at_dt, ttl_for_db)."""
    if expires_at:
        dt = _parse_expires_at(expires_at)
        if dt is None:
            raise ValueError("Format de date invalide (attendu AAAA-MM-JJ)")
        return (dt, None)
    if ttl_days is not None:
        cfg = settings().api_keys
        ttl = ttl_days if ttl_days in cfg.allowed_ttl_days else cfg.default_ttl_days
        return (None, None if ttl == 0 else ttl)
    if require_explicit:
        raise ValueError("Fournir ttl_days ou expires_at")
    cfg = settings().api_keys
    ttl = cfg.default_ttl_days
    return (None, None if ttl == 0 else ttl)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    body: ApiKeyCreateRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ApiKeyCreateResponse:
    """Crée une nouvelle clé API. La clé en clair n'est retournée qu'une seule fois."""
    max_keys = settings().api_keys.max_per_user
    async with get_async_session() as session:
        count = await count_api_keys_by_user(session, user_id)
        if count >= max_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de clés atteinte ({max_keys} maximum). Révoquez une clé existante pour en créer une nouvelle.",
            )
        if await exists_api_key_with_name(session, user_id, body.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Une clé avec le nom « {body.name} » existe déjà.",
            )
        try:
            expires_at_dt, ttl_for_create = _resolve_expiry_params(body.expires_at, body.ttl_days)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        try:
            api_key, plain_key = await create_api_key(
                session,
                user_id,
                body.name.strip(),
                ttl_days=ttl_for_create,
                tags=body.tags,
                description=body.description,
                expires_at=expires_at_dt,
            )
            await session.commit()
            return ApiKeyCreateResponse(
                id=str(api_key.id),
                key=plain_key,
                name=api_key.name,
                created_at=api_key.created_at,
                expires_at=api_key.expires_at,
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Une clé avec le nom « {body.name} » existe déjà.",
            )


@router.get("", response_model=ApiKeyListResponse)
async def list_keys(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ApiKeyListResponse:
    """Liste les clés API de l'utilisateur (sans valeur)."""
    async with get_async_session() as session:
        api_keys = await list_api_keys_by_user(session, user_id)
        items = [ApiKeyListItem.from_model(k) for k in api_keys]
        return ApiKeyListResponse(items=items)


def _build_update_kwargs(data: dict, expires_at_dt, ttl_for_update) -> dict:
    """Construit les kwargs pour update_api_key à partir des données de requête."""
    kwargs = {}
    if "name" in data and data["name"] is not None:
        kwargs["name"] = data["name"]
    if expires_at_dt is not None or ttl_for_update is not None:
        kwargs["expires_at"] = expires_at_dt
        kwargs["ttl_days"] = ttl_for_update
    if "tags" in data:
        kwargs["tags"] = data["tags"]
    if "description" in data:
        kwargs["description"] = data["description"]
    return kwargs


@router.patch("/{api_key_id}", response_model=ApiKeyListItem)
async def update_key(
    api_key_id: uuid.UUID,
    body: ApiKeyUpdateRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ApiKeyListItem:
    """Modifie une clé API (nom, validité, tags, description)."""
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune modification fournie",
        )
    expires_at_dt, ttl_for_update = None, None
    if "expires_at" in data or "ttl_days" in data:
        try:
            expires_at_dt, ttl_for_update = _resolve_expiry_params(data.get("expires_at"), data.get("ttl_days"), require_explicit=True)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    kwargs = _build_update_kwargs(data, expires_at_dt, ttl_for_update)
    async with get_async_session() as session:
        if "name" in data and data["name"] is not None and await exists_api_key_with_name(session, user_id, data["name"], exclude_id=api_key_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Une clé avec le nom « {data['name']} » existe déjà.",
            )
        api_key = await update_api_key(session, api_key_id, user_id, **kwargs)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clé non trouvée",
            )
        await session.commit()
        return ApiKeyListItem.from_model(api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    api_key_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Révoque une clé API."""
    async with get_async_session() as session:
        deleted = await delete_api_key(session, api_key_id, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clé non trouvée",
            )
        await session.commit()
