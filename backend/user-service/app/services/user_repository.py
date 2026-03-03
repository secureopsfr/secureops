"""Repository pour la gestion des utilisateurs en base de données."""

import logging
from typing import Optional

from common.logging_config import mask_email
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.services.subscription_repository import get_or_create_subscription

logger = logging.getLogger(__name__)


async def get_user_by_id(session: AsyncSession, user_id) -> Optional[User]:
    """Récupère un utilisateur par son ID.

    Args:
        session: Session de base de données.
        user_id: UUID de l'utilisateur.

    Returns:
        User ou None.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_cognito_sub(session: AsyncSession, cognito_sub: str) -> Optional[User]:
    """Récupère un utilisateur par son cognito_sub.

    Args:
        session (AsyncSession): Session de base de données.
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.

    Returns:
        Optional[User]: L'utilisateur trouvé ou None.
    """
    result = await session.execute(select(User).where(User.cognito_sub == cognito_sub))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, cognito_sub: str, email: str) -> User:
    """Crée un nouvel utilisateur en base de données.

    Args:
        session (AsyncSession): Session de base de données.
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.
        email (str): Email de l'utilisateur.

    Returns:
        User: L'utilisateur créé.

    Raises:
        ValueError: Si l'utilisateur existe déjà.
    """
    # Vérifier si l'utilisateur existe déjà
    existing_user = await get_user_by_cognito_sub(session, cognito_sub)
    if existing_user:
        raise ValueError(f"Utilisateur avec cognito_sub {cognito_sub} existe déjà")

    user = User(cognito_sub=cognito_sub, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info("Utilisateur créé en base: id=%s, cognito_sub=%s, email=%s", user.id, cognito_sub, mask_email(email))
    return user


async def _update_user_email_if_needed(session: AsyncSession, user: User, email: str) -> None:
    """Met à jour l'email d'un utilisateur si nécessaire.

    Args:
        session (AsyncSession): Session de base de données.
        user (User): Utilisateur à mettre à jour.
        email (str): Nouvel email.
    """
    if user.email != email:
        logger.info("Mise à jour email pour %s: %s -> %s", user.cognito_sub, mask_email(user.email), mask_email(email))
        user.email = email
        await session.commit()
        await session.refresh(user)


async def _create_user_with_subscription(session: AsyncSession, cognito_sub: str, email: str) -> User:
    """Crée un nouvel utilisateur avec son abonnement par défaut.

    Args:
        session (AsyncSession): Session de base de données.
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.
        email (str): Email de l'utilisateur.

    Returns:
        User: L'utilisateur créé.
    """
    new_user = await create_user(session, cognito_sub, email)
    logger.info("Utilisateur créé avec succès: id=%s", new_user.id)

    # Créer l'abonnement par défaut (free, active) pour le nouvel utilisateur
    try:
        subscription = await get_or_create_subscription(session, new_user.id, plan="free", status="active")
        logger.info("Abonnement créé pour l'utilisateur %s: plan=%s, status=%s", new_user.id, subscription.plan, subscription.status)
    except Exception as e:
        # Ne pas bloquer la création de l'utilisateur si l'abonnement échoue
        logger.error("Erreur lors de la création de l'abonnement pour %s: %s", new_user.id, e, exc_info=True)

    return new_user


async def _handle_race_condition(session: AsyncSession, cognito_sub: str, email: str) -> tuple[User, bool]:
    """Gère le cas où l'utilisateur a été créé entre-temps (race condition).

    Args:
        session (AsyncSession): Session de base de données.
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.
        email (str): Email de l'utilisateur.

    Returns:
        tuple[User, bool]: L'utilisateur existant et False (pas nouveau).

    Raises:
        IntegrityError: Si l'utilisateur n'a pas pu être récupéré.
    """
    logger.warning("Utilisateur créé entre-temps (race condition), récupération: cognito_sub=%s", cognito_sub)
    await session.rollback()
    existing_user = await get_user_by_cognito_sub(session, cognito_sub)
    if existing_user:
        await _update_user_email_if_needed(session, existing_user, email)
        return existing_user, False
    # Si on ne trouve toujours pas l'utilisateur, relancer l'exception
    logger.error("Impossible de récupérer l'utilisateur après erreur d'intégrité: cognito_sub=%s", cognito_sub)
    raise IntegrityError("Utilisateur non trouvé après race condition", None, None)


async def get_or_create_user(session: AsyncSession, cognito_sub: str, email: str) -> tuple[User, bool]:
    """Récupère un utilisateur ou le crée s'il n'existe pas (lazy creation).

    Args:
        session (AsyncSession): Session de base de données.
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.
        email (str): Email de l'utilisateur.

    Returns:
        tuple[User, bool]: L'utilisateur existant ou nouvellement créé, et un booléen indiquant si l'utilisateur vient d'être créé.
    """
    try:
        user = await get_user_by_cognito_sub(session, cognito_sub)
        logger.info("Recherche utilisateur: cognito_sub=%s, trouvé=%s", cognito_sub, user is not None)

        if user:
            await _update_user_email_if_needed(session, user, email)
            return user, False

        # Créer l'utilisateur s'il n'existe pas
        logger.info("Création nouvel utilisateur: cognito_sub=%s, email=%s", cognito_sub, mask_email(email))
        try:
            new_user = await _create_user_with_subscription(session, cognito_sub, email)
            return new_user, True
        except IntegrityError as e:
            # Gérer le cas où l'utilisateur a été créé entre-temps (race condition)
            if "uq_users_cognito_sub" in str(e.orig) or "duplicate key" in str(e.orig).lower():
                return await _handle_race_condition(session, cognito_sub, email)
            # Pour les autres erreurs d'intégrité, relancer l'exception
            raise
    except Exception as e:
        logger.error("Erreur dans get_or_create_user pour %s: %s", cognito_sub, e, exc_info=True)
        raise


async def update_user_language(session: AsyncSession, user: User, language: str) -> User:
    """Met à jour la préférence de langue d'un utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user (User): Utilisateur à mettre à jour.
        language (str): Code langue (fr ou en).

    Returns:
        User: L'utilisateur mis à jour.
    """
    user.language = language
    await session.commit()
    await session.refresh(user)
    logger.info("Préférence de langue mise à jour pour %s: language=%s", user.cognito_sub, language)
    return user


async def update_user_dark_mode(session: AsyncSession, user: User, dark_mode: bool) -> User:
    """Met à jour la préférence de thème d'un utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user (User): Utilisateur à mettre à jour.
        dark_mode (bool): True pour le mode sombre, False pour le mode clair.

    Returns:
        User: L'utilisateur mis à jour.
    """
    user.dark_mode = dark_mode
    await session.commit()
    await session.refresh(user)
    logger.info("Préférence de thème mise à jour pour %s: dark_mode=%s", user.cognito_sub, dark_mode)
    return user


async def delete_user_by_id(session: AsyncSession, user_id) -> bool:
    """Supprime un utilisateur de la base de données.

    Les relations cascade (favoris, abonnement) seront automatiquement supprimées.

    Args:
        session (AsyncSession): Session de base de données.
        user_id: UUID de l'utilisateur à supprimer.

    Returns:
        bool: True si l'utilisateur a été supprimé, False s'il n'existe pas.
    """
    # Charger l'utilisateur avec ses relations pour que SQLAlchemy puisse gérer la cascade
    result = await session.execute(select(User).where(User.id == user_id).options(selectinload(User.subscription), selectinload(User.favorites)))
    user = result.scalar_one_or_none()

    if not user:
        return False

    await session.delete(user)
    await session.commit()

    logger.info("Utilisateur supprimé de la base de données: id=%s, cognito_sub=%s", user_id, user.cognito_sub)
    return True
