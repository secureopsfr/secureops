"""Repository pour la gestion des clés API en base de données."""

import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.api_key import ApiKey

logger = logging.getLogger(__name__)

KEY_PREFIX = "sk_"
RANDOM_BYTES = 24  # token_urlsafe(24) → ~32 caractères


def _hash_key(key: str) -> str:
    """Retourne le hash SHA-256 de la clé (hex)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Génère une nouvelle clé API.

    Returns:
        tuple[str, str, str]: (clé_complète, key_hash, prefix)
    """
    random_part = secrets.token_urlsafe(RANDOM_BYTES)
    full_key = f"{KEY_PREFIX}{random_part}"
    key_hash = _hash_key(full_key)
    # Préfixe affiché : sk_ + 4 premiers caractères du random
    prefix = f"{KEY_PREFIX}{random_part[:4]}"
    return full_key, key_hash, prefix


def verify_key_against_hash(plain_key: str, stored_hash: str) -> bool:
    """Vérifie qu'une clé en clair correspond au hash stocké (comparaison en temps constant)."""
    computed = _hash_key(plain_key)
    return secrets.compare_digest(computed, stored_hash)


async def count_api_keys_by_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Compte le nombre de clés API de l'utilisateur."""
    result = await session.execute(select(func.count()).select_from(ApiKey).where(ApiKey.user_id == user_id))
    return result.scalar() or 0


async def create_api_key(
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    ttl_days: Optional[int] = 30,
    tags: Optional[list[str]] = None,
    description: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> tuple[ApiKey, str]:
    """Crée une nouvelle clé API.

    Args:
        session: Session async.
        user_id: UUID de l'utilisateur.
        name: Nom de la clé.
        ttl_days: Durée de validité en jours (None = pas d'expiration). Défaut: 30. Ignoré si expires_at fourni.
        tags: Tags optionnels (ex. ["production", "CI"]).
        description: Description optionnelle.
        expires_at: Date/heure d'expiration explicite (prioritaire sur ttl_days).

    Returns:
        tuple[ApiKey, str]: (entité créée, clé en clair à afficher une seule fois)
    """
    full_key, key_hash, prefix = generate_api_key()
    now = datetime.now(UTC)
    if expires_at is not None:
        final_expires_at = expires_at
    elif ttl_days:
        final_expires_at = now + timedelta(days=ttl_days)
    else:
        final_expires_at = None
    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        name=name.strip(),
        prefix=prefix,
        expires_at=final_expires_at,
        tags=tags if tags else None,
        description=description.strip() if description and description.strip() else None,
    )
    session.add(api_key)
    await session.flush()
    await session.refresh(api_key)
    return api_key, full_key


async def exists_api_key_with_name(
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    exclude_id: uuid.UUID | None = None,
) -> bool:
    """Vérifie si une clé avec ce nom existe déjà pour l'utilisateur (optionnellement en excluant un id)."""
    q = select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.name == name.strip())
    if exclude_id:
        q = q.where(ApiKey.id != exclude_id)
    result = await session.execute(q)
    return result.scalar_one_or_none() is not None


async def list_api_keys_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    """Liste les clés API de l'utilisateur."""
    result = await session.execute(select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc()))
    return list(result.scalars().all())


async def get_api_key_by_id(
    session: AsyncSession,
    api_key_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[ApiKey]:
    """Récupère une clé par ID si elle appartient à l'utilisateur."""
    result = await session.execute(select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user_id))
    return result.scalar_one_or_none()


async def get_api_key_by_hash(session: AsyncSession, key_hash: str) -> Optional[ApiKey]:
    """Récupère une clé par son hash (pour vérification). Charge user pour éviter lazy load async."""
    result = await session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash).options(selectinload(ApiKey.user)))
    return result.scalar_one_or_none()


async def get_api_key_by_plain_key(
    session: AsyncSession,
    plain_key: str,
) -> Optional[ApiKey]:
    """Récupère une clé par la clé en clair (hash + lookup)."""
    key_hash = _hash_key(plain_key)
    return await get_api_key_by_hash(session, key_hash)


async def delete_api_key(
    session: AsyncSession,
    api_key_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Supprime une clé si elle appartient à l'utilisateur.

    Returns:
        bool: True si supprimée, False si non trouvée.
    """
    api_key = await get_api_key_by_id(session, api_key_id, user_id)
    if not api_key:
        return False
    await session.delete(api_key)
    await session.flush()
    return True


def _parse_expires_at(date_str: str | None) -> datetime | None:
    """Parse une date AAAA-MM-JJ en datetime fin de journée UTC."""
    if not date_str or not date_str.strip():
        return None
    try:
        # Fin de journée 23:59:59 en UTC
        return datetime.strptime(date_str.strip() + " 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return None


async def update_api_key_expires_at(
    session: AsyncSession,
    api_key_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    ttl_days: Optional[int] = None,
    expires_at: Optional[datetime] = None,
) -> Optional[ApiKey]:
    """Met à jour la date d'expiration d'une clé API.

    Args:
        session: Session async.
        api_key_id: UUID de la clé.
        user_id: UUID de l'utilisateur (vérifie la propriété).
        ttl_days: Nouvelle durée en jours (None ou 0 = pas d'expiration).
        expires_at: Date/heure d'expiration explicite (prioritaire sur ttl_days).

    Returns:
        ApiKey mis à jour ou None si non trouvée.
    """
    api_key = await get_api_key_by_id(session, api_key_id, user_id)
    if not api_key:
        return None
    if expires_at is not None:
        api_key.expires_at = expires_at
    elif ttl_days:
        now = datetime.now(UTC)
        api_key.expires_at = now + timedelta(days=ttl_days)
    else:
        api_key.expires_at = None
    await session.flush()
    await session.refresh(api_key)
    return api_key


async def update_api_key(
    session: AsyncSession,
    api_key_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    name: str | None = None,
    ttl_days: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    tags: Optional[list[str]] = None,
    description: Optional[str] = None,
) -> Optional[ApiKey]:
    """Met à jour une clé API. Seules les valeurs fournies (non-None) sont modifiées.

    Pour tags, passer [] pour vider. Pour description, passer "" pour vider.
    Pour expires_at, ttl_days: applique la même logique que update_api_key_expires_at.
    """
    api_key = await get_api_key_by_id(session, api_key_id, user_id)
    if not api_key:
        return None
    if name is not None:
        api_key.name = name.strip()
    if expires_at is not None:
        api_key.expires_at = expires_at
    elif ttl_days is not None:
        if ttl_days:
            api_key.expires_at = datetime.now(UTC) + timedelta(days=ttl_days)
        else:
            api_key.expires_at = None
    if tags is not None:
        api_key.tags = tags if tags else None
    if description is not None:
        api_key.description = description.strip() if description and description.strip() else None
    await session.flush()
    await session.refresh(api_key)
    return api_key


async def update_last_used_at(session: AsyncSession, api_key: ApiKey) -> None:
    """Met à jour last_used_at pour une clé."""
    from datetime import UTC, datetime

    api_key.last_used_at = datetime.now(UTC)
    await session.flush()
