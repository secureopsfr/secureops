"""Router pour le journal d'audit des actions admin."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.audit_service import get_audit_logs, get_audit_stats

# Variables pour éviter B008
DEFAULT_LIMIT = Query(100, ge=1, le=500, description="Nombre maximum de résultats")
DEFAULT_OFFSET = Query(0, ge=0, description="Décalage pour la pagination")

router = APIRouter(prefix="/audit", tags=["audit", "admin"])


@router.get("")
async def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filtrer par type d'entité"),  # noqa: B008
    action: Optional[str] = Query(None, description="Filtrer par type d'action"),  # noqa: B008
    admin_email: Optional[str] = Query(None, description="Filtrer par admin"),  # noqa: B008
    entity_id: Optional[str] = Query(None, description="Filtrer par entité"),  # noqa: B008
    window_minutes: Optional[int] = Query(None, ge=1, description="Fenêtre temporelle en minutes"),  # noqa: B008
    limit: int = DEFAULT_LIMIT,
    offset: int = DEFAULT_OFFSET,
) -> Dict[str, Any]:
    """Récupère le journal d'audit avec filtres optionnels.

    Args:
        entity_type: Filtrer par type d'entité (user, contact, newsletter, etc.)
        action: Filtrer par action (user.ban, contact.status_change, etc.)
        admin_email: Filtrer par email admin
        entity_id: Filtrer par ID d'entité
        window_minutes: Fenêtre temporelle
        limit: Pagination - nombre max
        offset: Pagination - décalage

    Returns:
        dict: {logs: [...], total: int}
    """
    try:
        return await get_audit_logs(
            entity_type=entity_type,
            action=action,
            admin_email=admin_email,
            entity_id=entity_id,
            window_minutes=window_minutes,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/stats")
async def audit_stats(
    window_minutes: Optional[int] = Query(None, ge=1, description="Fenêtre temporelle en minutes"),  # noqa: B008
) -> Dict[str, Any]:
    """Récupère les statistiques d'audit agrégées.

    Args:
        window_minutes: Fenêtre temporelle

    Returns:
        dict: Statistiques d'audit
    """
    try:
        return await get_audit_stats(window_minutes=window_minutes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
