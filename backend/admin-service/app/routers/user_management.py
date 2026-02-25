"""Router pour les routes admin de gestion des utilisateurs."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.audit_service import log_action
from app.services.user_management_service import UserManagementService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_50 = Query(50, ge=1, le=200, description="Nombre maximum de résultats")
DEFAULT_QUERY_0 = Query(0, ge=0, description="Décalage pour la pagination")
DEFAULT_QUERY_NONE_STR = Query(None, description="Terme de recherche")

router = APIRouter(prefix="/users", tags=["users", "admin"])

# Instance du service
user_service = UserManagementService()


class UpdateGroupRequest(BaseModel):
    """Schéma de requête pour changer le groupe d'un utilisateur."""

    group: str


class ToggleStatusRequest(BaseModel):
    """Schéma de requête pour activer/désactiver un utilisateur."""

    action: str  # "disable" ou "enable"


@router.get("")
async def get_users(
    search: Optional[str] = DEFAULT_QUERY_NONE_STR,
    plan: Optional[str] = Query(None, description="Filtrer par plan (free, premium)"),  # noqa: B008
    status: Optional[str] = Query(None, description="Filtrer par statut (active, canceled, trial, suspended)"),  # noqa: B008
    limit: int = DEFAULT_QUERY_50,
    offset: int = DEFAULT_QUERY_0,
) -> Dict[str, Any]:
    """
    Récupère la liste des utilisateurs inscrits (admin uniquement).

    Args:
        search: Terme de recherche (email)
        plan: Filtrer par plan d'abonnement
        status: Filtrer par statut d'abonnement
        limit: Nombre maximum de résultats
        offset: Décalage pour la pagination

    Returns:
        dict: Liste des utilisateurs et total
    """
    try:
        result = user_service.get_users(
            search=search,
            plan_filter=plan,
            status_filter=status,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.get("/stats")
async def get_users_stats() -> Dict[str, Any]:
    """
    Récupère les statistiques globales des utilisateurs (admin uniquement).

    Returns:
        dict: Statistiques agrégées
    """
    try:
        return user_service.get_users_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.get("/{user_id}")
async def get_user_detail(user_id: str) -> Dict[str, Any]:
    """
    Récupère le détail d'un utilisateur (admin uniquement).

    Args:
        user_id: UUID de l'utilisateur

    Returns:
        dict: Détail complet de l'utilisateur
    """
    try:
        return user_service.get_user_detail(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.put("/{user_id}/group")
async def update_user_group(user_id: str, request: UpdateGroupRequest) -> Dict[str, Any]:
    """
    Change le groupe Cognito d'un utilisateur (admin uniquement).

    Args:
        user_id: UUID de l'utilisateur
        request: Nouveau groupe

    Returns:
        dict: Résultat de l'opération
    """
    try:
        result = user_service.update_user_group(user_id, request.group)
        await log_action(
            admin_email="admin",
            action="user.group_change",
            entity_type="user",
            entity_id=user_id,
            details={"new_group": request.group},
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.put("/{user_id}/status")
async def toggle_user_status(user_id: str, request: ToggleStatusRequest) -> Dict[str, Any]:
    """
    Active ou désactive un utilisateur (admin uniquement).

    Args:
        user_id: UUID de l'utilisateur
        request: Action (disable / enable)

    Returns:
        dict: Résultat de l'opération
    """
    try:
        result = user_service.toggle_user_status(user_id, request.action)
        action = "user.ban" if request.action == "disable" else "user.unban"
        await log_action(
            admin_email="admin",
            action=action,
            entity_type="user",
            entity_id=user_id,
            details={"action": request.action},
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")
