"""Router pour les routes admin de gestion des abonnements."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.audit_service import log_action
from app.services.subscription_service import SubscriptionService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_50 = Query(50, ge=1, le=200, description="Nombre maximum de résultats")
DEFAULT_QUERY_0 = Query(0, ge=0, description="Décalage pour la pagination")
DEFAULT_QUERY_NONE_STR = Query(None, description="Terme de recherche")

router = APIRouter(prefix="/subscriptions", tags=["subscriptions", "admin"])

# Instance du service
subscription_service = SubscriptionService()


class UpdateSubscriptionRequest(BaseModel):
    """Schéma de requête pour mettre à jour un abonnement."""

    plan: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[str] = None


@router.get("")
async def get_subscriptions(
    plan: Optional[str] = Query(None, description="Filtrer par plan (free, premium)"),  # noqa: B008
    status: Optional[str] = Query(None, description="Filtrer par statut (active, canceled, trial, suspended)"),  # noqa: B008
    search: Optional[str] = DEFAULT_QUERY_NONE_STR,
    has_stripe: Optional[bool] = Query(None, description="Filtrer par présence Stripe"),  # noqa: B008
    limit: int = DEFAULT_QUERY_50,
    offset: int = DEFAULT_QUERY_0,
) -> Dict[str, Any]:
    """
    Récupère la liste des abonnements (admin uniquement).

    Args:
        plan: Filtrer par plan
        status: Filtrer par statut
        search: Recherche par email
        has_stripe: Filtrer par présence Stripe
        limit: Nombre maximum de résultats
        offset: Décalage pour la pagination

    Returns:
        dict: Liste des abonnements et total
    """
    try:
        return subscription_service.get_subscriptions(
            plan_filter=plan,
            status_filter=status,
            search=search,
            has_stripe=has_stripe,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.get("/stats")
async def get_subscription_stats() -> Dict[str, Any]:
    """
    Récupère les statistiques globales des abonnements (admin uniquement).

    Returns:
        dict: Statistiques agrégées (plans, statuts, MRR, churn, conversion, historique)
    """
    try:
        return subscription_service.get_subscription_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.get("/history")
async def get_plan_history(
    limit: int = DEFAULT_QUERY_50,
    offset: int = DEFAULT_QUERY_0,
) -> Dict[str, Any]:
    """
    Récupère l'historique des changements d'abonnements (admin uniquement).

    Returns:
        dict: Historique des changements et total
    """
    try:
        return subscription_service.get_plan_history(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.put("/{subscription_id}")
async def update_subscription(subscription_id: str, request: UpdateSubscriptionRequest) -> Dict[str, Any]:
    """
    Met à jour un abonnement (admin uniquement).

    Args:
        subscription_id: UUID de l'abonnement
        request: Champs à mettre à jour (plan, status, current_period_end)

    Returns:
        dict: Abonnement mis à jour
    """
    updates: Dict[str, Any] = {}
    if request.plan is not None:
        updates["plan"] = request.plan
    if request.status is not None:
        updates["status"] = request.status
    if request.current_period_end is not None:
        updates["current_period_end"] = request.current_period_end

    if not updates:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    try:
        result = subscription_service.update_subscription(subscription_id, updates)
        await log_action(
            admin_email="admin",
            action="subscription.update",
            entity_type="subscription",
            entity_id=subscription_id,
            details=updates,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")
