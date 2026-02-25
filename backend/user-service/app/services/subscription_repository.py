"""Repository pour la gestion des abonnements en base de données."""

import logging
import uuid
from datetime import datetime
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription

logger = logging.getLogger(__name__)


async def get_subscription_by_user_id(session: AsyncSession, user_id: Union[uuid.UUID, str]) -> Optional[Subscription]:
    """Récupère un abonnement par l'ID de l'utilisateur.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (Union[uuid.UUID, str]): UUID de l'utilisateur.

    Returns:
        Optional[Subscription]: L'abonnement trouvé ou None.
    """
    # Convertir en UUID si nécessaire
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    return result.scalar_one_or_none()


async def create_subscription(
    session: AsyncSession,
    user_id: Union[uuid.UUID, str],
    plan: str = "free",
    status: str = "active",
    stripe_customer_id: Optional[str] = None,
    current_period_end: Optional[datetime] = None,
    newsletter_enabled: bool = False,
    new_features_notifications_enabled: bool = False,
) -> Subscription:
    """Crée un nouvel abonnement en base de données.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (Union[uuid.UUID, str]): UUID de l'utilisateur.
        plan (str): Plan d'abonnement (free / premium). Par défaut "free".
        status (str): Statut de l'abonnement (active / canceled / trial). Par défaut "active".
        stripe_customer_id (Optional[str]): Identifiant Stripe du client. Par défaut None.
        current_period_end (Optional[datetime]): Date de fin de la période courante. Par défaut None.
        newsletter_enabled (bool): Inscription à la newsletter. Par défaut False.
        new_features_notifications_enabled (bool): Notifications par mail pour nouvelles données ou features. Par défaut False.

    Returns:
        Subscription: L'abonnement créé.

    Raises:
        ValueError: Si l'abonnement existe déjà pour cet utilisateur.
    """
    # Convertir en UUID si nécessaire
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    # Vérifier si l'abonnement existe déjà
    existing_subscription = await get_subscription_by_user_id(session, user_id)
    if existing_subscription:
        raise ValueError(f"Abonnement pour user_id {user_id} existe déjà")

    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        status=status,
        stripe_customer_id=stripe_customer_id,
        current_period_end=current_period_end,
        newsletter_enabled=newsletter_enabled,
        new_features_notifications_enabled=new_features_notifications_enabled,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)

    logger.info("Abonnement créé en base: id=%s, user_id=%s, plan=%s, status=%s", subscription.id, user_id, plan, status)
    return subscription


async def get_or_create_subscription(
    session: AsyncSession,
    user_id: Union[uuid.UUID, str],
    plan: str = "free",
    status: str = "active",
) -> Subscription:
    """Récupère un abonnement ou le crée s'il n'existe pas.

    Args:
        session (AsyncSession): Session de base de données.
        user_id (Union[uuid.UUID, str]): UUID de l'utilisateur.
        plan (str): Plan d'abonnement (free / premium). Par défaut "free".
        status (str): Statut de l'abonnement (active / canceled / trial). Par défaut "active".

    Returns:
        Subscription: L'abonnement existant ou nouvellement créé.
    """
    subscription = await get_subscription_by_user_id(session, user_id)

    if subscription:
        return subscription

    # Créer l'abonnement avec les valeurs par défaut pour un plan free
    return await create_subscription(session, user_id, plan=plan, status=status)
