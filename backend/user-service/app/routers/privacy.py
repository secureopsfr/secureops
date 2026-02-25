"""Endpoints liés à la vie privée (export des données personnelles)."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.db import get_async_session
from app.services.favorite_repository import get_user_favorites
from app.services.subscription_repository import get_subscription_by_user_id
from app.services.user_repository import get_user_by_cognito_sub
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user – vie privée"])


@router.get("/export", response_class=PlainTextResponse)
async def export_user_data(
    current_user: Annotated[Dict, Depends(get_current_user)],
) -> PlainTextResponse:
    """Exporte toutes les données personnelles de l'utilisateur (RGPD)."""
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

            # Profil (sans ID ni cognito_sub)
            profile_data = {
                "email": user.email,
                "dark_mode": user.dark_mode if user.dark_mode is not None else True,
                "language": user.language if user.language else "fr",
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

            # Abonnement (sans ID ni stripe_customer_id)
            subscription = await get_subscription_by_user_id(session, user.id)
            if subscription:
                subscription_data = {
                    "plan": subscription.plan,
                    "status": subscription.status,
                    "newsletter_enabled": subscription.newsletter_enabled,
                    "new_features_notifications_enabled": subscription.new_features_notifications_enabled,
                    "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                    "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
                    "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                }
            else:
                subscription_data = {
                    "plan": "free",
                    "status": "active",
                    "newsletter_enabled": False,
                    "new_features_notifications_enabled": False,
                    "created_at": None,
                    "updated_at": None,
                    "current_period_end": None,
                }

            # Favoris (sans ID ni user_id)
            favorites = await get_user_favorites(session, user.id, limit=1000)
            favorites_data = [
                {
                    "search_type": favorite.search_type,
                    "query_json": favorite.query_json,
                    "created_at": favorite.created_at.isoformat() if favorite.created_at else None,
                }
                for favorite in favorites
            ]

            export_date = datetime.now(UTC).isoformat()
            lines = [
                "Profil:",
                f"  email: {profile_data['email']}",
                f"  dark_mode: {profile_data['dark_mode']}",
                f"  language: {profile_data['language']}",
                f"  created_at: {profile_data.get('created_at') or 'N/A'}",
                "",
                "Abonnement:",
                f"  plan: {subscription_data['plan']}",
                f"  status: {subscription_data['status']}",
                f"  newsletter_enabled: {subscription_data['newsletter_enabled']}",
                f"  new_features_notifications_enabled: {subscription_data['new_features_notifications_enabled']}",
                f"  created_at: {subscription_data.get('created_at') or 'N/A'}",
                f"  updated_at: {subscription_data.get('updated_at') or 'N/A'}",
                f"  current_period_end: {subscription_data.get('current_period_end') or 'N/A'}",
                "",
                "Favoris:",
            ]

            if favorites_data:
                for index, favorite in enumerate(favorites_data, start=1):
                    lines.append(f"  Favori {index}:")
                    lines.append(f"    search_type: {favorite['search_type']}")
                    lines.append(f"    query_json: {favorite['query_json']}")
                    lines.append(f"    created_at: {favorite.get('created_at') or 'N/A'}")
            else:
                lines.append("  Aucun favori enregistré.")

            lines.extend(["", f"Date d'export: {export_date}"])

            return PlainTextResponse(content="\n".join(lines))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur lors de l'export des données utilisateur: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'export des données",
        )
