"""Router pour le système d'alertes et monitoring proactif."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.alerting_service import (
    acknowledge_alert,
    acknowledge_all_alerts,
    check_alerts,
    create_alert_rule,
    delete_alert_rule,
    get_alert_events,
    get_alert_rules,
    get_alert_summary,
    toggle_alert_rule,
    update_alert_rule,
)

# Variables pour éviter B008
DEFAULT_LIMIT = Query(50, ge=1, le=200, description="Nombre maximum de résultats")
DEFAULT_OFFSET = Query(0, ge=0, description="Décalage pour la pagination")

router = APIRouter(prefix="/alerts", tags=["alerts", "admin"])


# ─────────────────────── Schémas ───────────────────────


class CreateAlertRuleRequest(BaseModel):
    """Requête de création d'une règle d'alerte."""

    name: str
    metric: str  # error_rate, response_time, error_count, request_count
    condition: str = "gt"  # gt, lt, eq, gte, lte
    threshold: float
    window_minutes: int = 5
    service_filter: Optional[str] = None
    notify_email: bool = True
    enabled: bool = True
    cooldown_minutes: int = 30


class UpdateAlertRuleRequest(BaseModel):
    """Requête de mise à jour d'une règle d'alerte."""

    name: Optional[str] = None
    metric: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    window_minutes: Optional[int] = None
    service_filter: Optional[str] = None
    notify_email: Optional[bool] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = None


class AcknowledgeRequest(BaseModel):
    """Requête d'acquittement d'une alerte."""

    admin_email: str


# ─────────────────────── Règles ───────────────────────


@router.get("/rules")
async def list_rules() -> List[Dict[str, Any]]:
    """Récupère toutes les règles d'alerte."""
    try:
        return await get_alert_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules")
async def create_rule(request: CreateAlertRuleRequest) -> Dict[str, Any]:
    """Crée une nouvelle règle d'alerte."""
    try:
        return await create_alert_rule(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, request: UpdateAlertRuleRequest) -> Dict[str, Any]:
    """Met à jour une règle d'alerte."""
    try:
        data = {k: v for k, v in request.model_dump().items() if v is not None}
        return await update_alert_rule(rule_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def remove_rule(rule_id: str) -> Dict[str, bool]:
    """Supprime une règle d'alerte."""
    try:
        deleted = await delete_alert_rule(rule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Règle introuvable")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str) -> Dict[str, Any]:
    """Active ou désactive une règle d'alerte."""
    try:
        return await toggle_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────── Événements ───────────────────────


@router.get("/events")
async def list_events(
    severity: Optional[str] = Query(None, description="Filtrer par gravité"),  # noqa: B008
    acknowledged: Optional[bool] = Query(None, description="Filtrer par acquittement"),  # noqa: B008
    limit: int = DEFAULT_LIMIT,
    offset: int = DEFAULT_OFFSET,
) -> Dict[str, Any]:
    """Récupère les événements d'alerte."""
    try:
        return await get_alert_events(
            severity=severity,
            acknowledged=acknowledged,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/{event_id}/acknowledge")
async def ack_event(event_id: str, request: AcknowledgeRequest) -> Dict[str, Any]:
    """Acquitte une alerte spécifique."""
    try:
        return await acknowledge_alert(event_id, request.admin_email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/acknowledge-all")
async def ack_all(request: AcknowledgeRequest) -> Dict[str, Any]:
    """Acquitte toutes les alertes non acquittées."""
    try:
        count = await acknowledge_all_alerts(request.admin_email)
        return {"success": True, "acknowledged_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────── Check & Summary ───────────────────────


@router.post("/check")
async def run_check() -> Dict[str, Any]:
    """Évalue toutes les règles actives et déclenche les alertes si nécessaire."""
    try:
        triggered = await check_alerts()
        return {"triggered": triggered, "count": len(triggered)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def summary() -> Dict[str, Any]:
    """Récupère un résumé rapide des alertes pour le dashboard."""
    try:
        return await get_alert_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
