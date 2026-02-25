"""Repository pour la gestion des favoris en base de données."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import cast, desc, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite

logger = logging.getLogger(__name__)


async def get_favorite_by_query(
    session: AsyncSession,
    user_id: uuid.UUID,
    search_type: str,
    query_json: Dict[str, Any],
) -> Optional[Favorite]:
    """Récupère une entrée de favori par user_id, search_type et query_json.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (uuid.UUID): UUID de l'utilisateur.
        search_type (str): Type de recherche effectuée.
        query_json (Dict[str, Any]): Données JSON de la requête.

    Returns:
        Optional[Favorite]: L'entrée de favori trouvée ou None.
    """
    # Comparer les JSONB avec l'opérateur @> dans les deux sens pour vérifier l'égalité exacte
    # (A @> B AND B @> A équivaut à A = B pour JSONB, indépendamment de l'ordre des clés)
    # Cela garantit que TOUS les query parameters sont identiques :
    # - Tous les paramètres de query_json sont présents dans Favorite.query_json avec les mêmes valeurs
    # - Tous les paramètres de Favorite.query_json sont présents dans query_json avec les mêmes valeurs
    # - Aucun paramètre supplémentaire ou manquant
    query_json_cast = cast(query_json, JSONB)
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.search_type == search_type,
            Favorite.query_json.contains(query_json),  # Favorite.query_json @> query_json
            query_json_cast.contains(Favorite.query_json),  # query_json @> Favorite.query_json
        )
    )
    return result.scalar_one_or_none()


def normalize_query_json(query_json: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise query_json pour une comparaison cohérente.

    Normalise notamment immosphere_ids pour qu'il soit toujours un tableau trié.

    Args:
        query_json (Dict[str, Any]): Données JSON de la requête.

    Returns:
        Dict[str, Any]: Données JSON normalisées.
    """
    normalized = query_json.copy()

    # Normaliser immosphere_ids : toujours un tableau trié
    if "immosphere_ids" in normalized:
        immosphere_ids = normalized["immosphere_ids"]
        if isinstance(immosphere_ids, str):
            # Si c'est une string, convertir en tableau
            normalized["immosphere_ids"] = [immosphere_ids] if immosphere_ids else []
        elif isinstance(immosphere_ids, list):
            # Si c'est un tableau, le trier
            normalized["immosphere_ids"] = sorted(immosphere_ids)
        else:
            # Sinon, tableau vide
            normalized["immosphere_ids"] = []

    return normalized


async def create_or_update_favorite(
    session: AsyncSession,
    user_id: uuid.UUID,
    search_type: str,
    query_json: Dict[str, Any],
) -> Favorite:
    """Crée une nouvelle entrée de favori ou met à jour une existante.

    Si une entrée existe déjà avec le même user_id, search_type et query_json,
    met à jour sa date created_at. Sinon, crée une nouvelle entrée.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (uuid.UUID): UUID de l'utilisateur.
        search_type (str): Type de recherche effectuée.
        query_json (Dict[str, Any]): Données JSON de la requête.

    Returns:
        Favorite: L'entrée de favori créée ou mise à jour.
    """
    # Normaliser query_json pour une comparaison cohérente
    normalized_query_json = normalize_query_json(query_json)

    # Chercher une entrée existante avec le query_json normalisé
    existing_favorite = await get_favorite_by_query(session, user_id, search_type, normalized_query_json)

    if existing_favorite:
        # Mettre à jour la date de création pour la remonter en haut des favoris
        existing_favorite.created_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(existing_favorite)

        logger.info("Favori mis à jour: id=%s, user_id=%s, search_type=%s", existing_favorite.id, user_id, search_type)
        return existing_favorite

    # Créer une nouvelle entrée avec le query_json normalisé
    favorite = Favorite(
        user_id=user_id,
        search_type=search_type,
        query_json=normalized_query_json,
    )
    session.add(favorite)
    await session.commit()
    await session.refresh(favorite)

    logger.info("Favori créé: id=%s, user_id=%s, search_type=%s", favorite.id, user_id, search_type)
    return favorite


async def get_user_favorites(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> List[Favorite]:
    """Récupère les favoris d'un utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (uuid.UUID): UUID de l'utilisateur.
        limit (int): Nombre maximum d'entrées à récupérer. Par défaut 100.
        offset (int): Nombre d'entrées à ignorer. Par défaut 0.

    Returns:
        List[Favorite]: Liste des entrées de favoris, triées par date de création décroissante.
    """
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id).order_by(desc(Favorite.created_at)).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def count_user_favorites(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """Compte le nombre total de favoris d'un utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (uuid.UUID): UUID de l'utilisateur.

    Returns:
        int: Nombre total de favoris.
    """
    result = await session.execute(select(func.count(Favorite.id)).where(Favorite.user_id == user_id))
    return result.scalar() or 0


async def delete_favorite_by_id(
    session: AsyncSession,
    favorite_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Supprime un favori par son ID, en vérifiant qu'il appartient à l'utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        favorite_id (uuid.UUID): UUID du favori à supprimer.
        user_id (uuid.UUID): UUID de l'utilisateur propriétaire.

    Returns:
        bool: True si le favori a été supprimé, False s'il n'existe pas ou n'appartient pas à l'utilisateur.
    """
    result = await session.execute(select(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == user_id))
    favorite = result.scalar_one_or_none()

    if not favorite:
        return False

    await session.delete(favorite)
    await session.commit()

    logger.info("Favori supprimé: id=%s, user_id=%s", favorite_id, user_id)
    return True


async def delete_user_favorites(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Supprime tous les favoris d'un utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (uuid.UUID): UUID de l'utilisateur.

    Returns:
        int: Nombre d'entrées supprimées.
    """
    result = await session.execute(select(Favorite).where(Favorite.user_id == user_id))
    favorites = list(result.scalars().all())

    for favorite in favorites:
        await session.delete(favorite)

    await session.commit()

    logger.info("Favoris supprimés pour user_id=%s: %s entrées", user_id, len(favorites))
    return len(favorites)
