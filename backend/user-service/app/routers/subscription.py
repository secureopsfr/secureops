"""Endpoints liés à l'abonnement utilisateur."""

import logging
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_async_session
from app.schemas.user import SubscriptionPreferencesUpdateRequest, SubscriptionResponse
from app.services.subscription_repository import get_subscription_by_user_id
from app.services.user_repository import get_user_by_cognito_sub
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – abonnement"])


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> SubscriptionResponse:
    """Récupère l'abonnement de l'utilisateur."""
    try:
        cognito_sub = current_user.get("sub")
        if not cognito_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossible d'identifier l'utilisateur",
            )

        async with get_async_session() as session:
            user = await get_user_by_cognito_sub(session, cognito_sub)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé en base de données",
                )

            subscription = await get_subscription_by_user_id(session, user.id)
            if not subscription:
                return SubscriptionResponse(
                    plan="free",
                    status="active",
                    stripe_customer_id=None,
                    current_period_end=None,
                    newsletter_enabled=False,
                    new_features_notifications_enabled=False,
                )

            return SubscriptionResponse(
                plan=subscription.plan,
                status=subscription.status,
                stripe_customer_id=subscription.stripe_customer_id,
                current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                newsletter_enabled=subscription.newsletter_enabled,
                new_features_notifications_enabled=subscription.new_features_notifications_enabled,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération de l'abonnement: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de l'abonnement",
        )


@router.patch("/subscription/preferences", response_model=SubscriptionResponse)
async def update_subscription_preferences(
    preferences: SubscriptionPreferencesUpdateRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> SubscriptionResponse:
    """Met à jour les préférences d'abonnement (newsletter, notifications)."""
    try:
        cognito_sub = current_user.get("sub")
        if not cognito_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossible d'identifier l'utilisateur",
            )

        async with get_async_session() as session:
            user = await get_user_by_cognito_sub(session, cognito_sub)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé en base de données",
                )

            subscription = await get_subscription_by_user_id(session, user.id)
            if not subscription:
                from app.services.subscription_repository import get_or_create_subscription

                subscription = await get_or_create_subscription(session, user.id)

            if preferences.newsletter_enabled is not None:
                subscription.newsletter_enabled = preferences.newsletter_enabled
            if preferences.new_features_notifications_enabled is not None:
                subscription.new_features_notifications_enabled = preferences.new_features_notifications_enabled

            await session.commit()
            await session.refresh(subscription)

            return SubscriptionResponse(
                plan=subscription.plan,
                status=subscription.status,
                stripe_customer_id=subscription.stripe_customer_id,
                current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                newsletter_enabled=subscription.newsletter_enabled,
                new_features_notifications_enabled=subscription.new_features_notifications_enabled,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la mise à jour des préférences d'abonnement: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour des préférences d'abonnement",
        )
