"""Endpoints liés à l'abonnement utilisateur."""

import logging
import uuid
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.schemas.user import SubscriptionPreferencesUpdateRequest, SubscriptionResponse
from app.services.scan_alert_repository import delete_alert_events_older_than_days, delete_all_alert_events_by_user
from app.services.scan_repository import delete_all_user_scans, delete_scans_older_than_days
from app.services.subscription_repository import get_subscription_by_user_id
from app.utils.auth import require_jwt_user, resolve_user

logger = logging.getLogger(__name__)

HISTORY_RETENTION_VALUES = frozenset({"none", "7", "30", "90", "365"})

router = APIRouter(prefix="/api/user", tags=["user – abonnement"])


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> SubscriptionResponse:
    """Récupère l'abonnement de l'utilisateur."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            subscription = await get_subscription_by_user_id(session, user.id)
            if not subscription:
                return SubscriptionResponse(
                    plan="free",
                    status="active",
                    stripe_customer_id=None,
                    current_period_end=None,
                    newsletter_enabled=False,
                    new_features_notifications_enabled=False,
                    history_retention="30",
                )

            return SubscriptionResponse(
                plan=subscription.plan,
                status=subscription.status,
                stripe_customer_id=subscription.stripe_customer_id,
                current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                newsletter_enabled=subscription.newsletter_enabled,
                new_features_notifications_enabled=subscription.new_features_notifications_enabled,
                history_retention=subscription.history_retention or "30",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la récupération de l'abonnement: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de l'abonnement",
        )


async def _apply_history_retention_cleanup(session: AsyncSession, user_id: uuid.UUID, retention: str) -> None:
    """Applique le nettoyage des scans et alertes selon la nouvelle durée de rétention."""
    if retention == "none":
        await delete_all_user_scans(session, user_id)
        await delete_all_alert_events_by_user(session, user_id)
    else:
        days = int(retention)
        await delete_scans_older_than_days(session, user_id, days)
        await delete_alert_events_older_than_days(session, user_id, days)


def _subscription_to_response(subscription) -> SubscriptionResponse:
    """Construit une SubscriptionResponse à partir d'un objet Subscription."""
    return SubscriptionResponse(
        plan=subscription.plan,
        status=subscription.status,
        stripe_customer_id=subscription.stripe_customer_id,
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        newsletter_enabled=subscription.newsletter_enabled,
        new_features_notifications_enabled=subscription.new_features_notifications_enabled,
        history_retention=subscription.history_retention or "30",
    )


async def _apply_preferences(
    session: AsyncSession,
    subscription,
    user_id: uuid.UUID,
    preferences: SubscriptionPreferencesUpdateRequest,
) -> None:
    """Applique les préférences à l'abonnement et exécute le nettoyage si nécessaire."""
    if preferences.newsletter_enabled is not None:
        subscription.newsletter_enabled = preferences.newsletter_enabled
    if preferences.new_features_notifications_enabled is not None:
        subscription.new_features_notifications_enabled = preferences.new_features_notifications_enabled
    if preferences.history_retention is not None:
        if preferences.history_retention not in HISTORY_RETENTION_VALUES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"history_retention doit être one of: {', '.join(sorted(HISTORY_RETENTION_VALUES))}",
            )
        subscription.history_retention = preferences.history_retention
        await _apply_history_retention_cleanup(session, user_id, preferences.history_retention)


@router.patch("/subscription/preferences", response_model=SubscriptionResponse)
async def update_subscription_preferences(
    preferences: SubscriptionPreferencesUpdateRequest,
    current_user: Annotated[Dict, Depends(require_jwt_user)],
) -> SubscriptionResponse:
    """Met à jour les préférences d'abonnement (newsletter, notifications)."""
    try:
        async with get_async_session() as session:
            user = await resolve_user(session, current_user)
            subscription = await get_subscription_by_user_id(session, user.id)
            if not subscription:
                from app.services.subscription_repository import get_or_create_subscription

                subscription = await get_or_create_subscription(session, user.id)

            await _apply_preferences(session, subscription, user.id, preferences)
            await session.commit()
            await session.refresh(subscription)
            return _subscription_to_response(subscription)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de la mise à jour des préférences d'abonnement: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour des préférences d'abonnement",
        )
