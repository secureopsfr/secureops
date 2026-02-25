"""Service de gestion des alertes et du monitoring proactif.

Fournit des fonctions pour :
- CRUD des règles d'alerte
- Évaluation des règles (check_alerts)
- Récupération des événements d'alerte
- Acquittement des alertes
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select, update

from app.db import get_async_session
from app.email_config import send_alert_email
from app.models.alert import AlertEvent, AlertRule
from app.models.http_request import HttpRequest

logger = logging.getLogger(__name__)


# ─────────────────────── Règles CRUD ───────────────────────


async def get_alert_rules() -> List[Dict[str, Any]]:
    """Récupère toutes les règles d'alerte.

    Returns:
        list: Liste des règles.
    """
    async with get_async_session() as session:
        result = await session.execute(select(AlertRule).order_by(desc(AlertRule.created_at)))
        rules = result.scalars().all()
        return [_serialize_rule(r) for r in rules]


async def create_alert_rule(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée une nouvelle règle d'alerte.

    Args:
        data: données de la règle.

    Returns:
        dict: règle créée.
    """
    async with get_async_session() as session:
        rule = AlertRule(
            name=data["name"],
            metric=data["metric"],
            condition=data.get("condition", "gt"),
            threshold=data["threshold"],
            window_minutes=data.get("window_minutes", 5),
            service_filter=data.get("service_filter"),
            notify_email=data.get("notify_email", True),
            enabled=data.get("enabled", True),
            cooldown_minutes=data.get("cooldown_minutes", 30),
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return _serialize_rule(rule)


async def update_alert_rule(rule_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Met à jour une règle d'alerte.

    Args:
        rule_id: UUID de la règle.
        data: champs à mettre à jour.

    Returns:
        dict: règle mise à jour.

    Raises:
        ValueError: si la règle n'existe pas.
    """
    async with get_async_session() as session:
        result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError(f"Règle {rule_id} introuvable")

        for key in ["name", "metric", "condition", "threshold", "window_minutes", "service_filter", "notify_email", "enabled", "cooldown_minutes"]:
            if key in data:
                setattr(rule, key, data[key])

        rule.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(rule)
        return _serialize_rule(rule)


async def delete_alert_rule(rule_id: str) -> bool:
    """Supprime une règle d'alerte.

    Args:
        rule_id: UUID de la règle.

    Returns:
        bool: True si supprimée.
    """
    async with get_async_session() as session:
        result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        await session.delete(rule)
        await session.commit()
        return True


async def toggle_alert_rule(rule_id: str) -> Dict[str, Any]:
    """Active/désactive une règle d'alerte.

    Args:
        rule_id: UUID de la règle.

    Returns:
        dict: règle mise à jour.
    """
    async with get_async_session() as session:
        result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError(f"Règle {rule_id} introuvable")

        rule.enabled = not rule.enabled
        rule.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(rule)
        return _serialize_rule(rule)


# ─────────────────────── Événements d'alerte ───────────────────────


async def get_alert_events(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Récupère les événements d'alerte.

    Args:
        severity: filtrer par gravité.
        acknowledged: filtrer par statut d'acquittement.
        limit: pagination.
        offset: pagination.

    Returns:
        dict: {events: [...], total: int}
    """
    async with get_async_session() as session:
        base = select(AlertEvent)
        count_q = select(func.count(AlertEvent.id))

        if severity:
            base = base.where(AlertEvent.severity == severity)
            count_q = count_q.where(AlertEvent.severity == severity)
        if acknowledged is not None:
            base = base.where(AlertEvent.acknowledged == acknowledged)
            count_q = count_q.where(AlertEvent.acknowledged == acknowledged)

        total_result = await session.execute(count_q)
        total = total_result.scalar() or 0

        stmt = base.order_by(desc(AlertEvent.created_at)).offset(offset).limit(limit)
        result = await session.execute(stmt)
        events = result.scalars().all()

        from app.schemas.common import make_pagination_meta

        return {
            "events": [_serialize_event(e) for e in events],
            **make_pagination_meta(total=total, limit=limit, offset=offset),
        }


async def acknowledge_alert(event_id: str, admin_email: str) -> Dict[str, Any]:
    """Acquitte une alerte.

    Args:
        event_id: UUID de l'événement.
        admin_email: email de l'admin.

    Returns:
        dict: événement mis à jour.
    """
    async with get_async_session() as session:
        result = await session.execute(select(AlertEvent).where(AlertEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError(f"Alerte {event_id} introuvable")

        event.acknowledged = True
        event.acknowledged_by = admin_email
        event.acknowledged_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(event)
        return _serialize_event(event)


async def acknowledge_all_alerts(admin_email: str) -> int:
    """Acquitte toutes les alertes non acquittées.

    Args:
        admin_email: email de l'admin.

    Returns:
        int: nombre d'alertes acquittées.
    """
    async with get_async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = (
            update(AlertEvent)
            .where(AlertEvent.acknowledged == False)  # noqa: E712
            .values(acknowledged=True, acknowledged_by=admin_email, acknowledged_at=now)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


# ─────────────────────── Évaluation des règles ───────────────────────


async def _evaluate_rule(session, rule: AlertRule) -> Optional[Dict[str, Any]]:
    """Évalue une règle d'alerte et crée un événement si le seuil est dépassé.

    Args:
        session: session SQLAlchemy active.
        rule: règle d'alerte à évaluer.

    Returns:
        dict | None: données de l'alerte déclenchée, ou None si pas de déclenchement.
    """
    if await _is_in_cooldown(session, rule):
        return None

    value = await _compute_metric(session, rule)
    if value is None:
        return None

    if not _check_condition(value, rule.condition, rule.threshold):
        return None

    severity = "critical" if rule.condition == "gt" and value > rule.threshold * 2 else "warning"
    message = _build_message(rule, value)

    event = AlertEvent(
        rule_id=rule.id,
        rule_name=rule.name,
        metric=rule.metric,
        current_value=value,
        threshold=rule.threshold,
        severity=severity,
        message=message,
    )
    session.add(event)

    _notify_if_needed(rule, value, severity, message)

    return _serialize_event_from_data(rule, value, severity, message)


def _notify_if_needed(rule: AlertRule, value: float, severity: str, message: str) -> None:
    """Envoie un email de notification si activé sur la règle."""
    if not rule.notify_email:
        return
    try:
        send_alert_email(
            rule_name=rule.name,
            metric=rule.metric,
            current_value=value,
            threshold=rule.threshold,
            severity=severity,
            message=message,
            window_minutes=rule.window_minutes,
            service_filter=rule.service_filter,
        )
    except Exception as email_err:
        logger.error("[Alerting] Échec envoi email pour règle %s: %s", rule.name, email_err)


async def check_alerts() -> List[Dict[str, Any]]:
    """Évalue toutes les règles actives et crée des événements d'alerte si nécessaire.

    Parcourt les règles actives, calcule la métrique sur la fenêtre temporelle,
    vérifie le cooldown, et crée un AlertEvent si le seuil est dépassé.

    Returns:
        list: liste des nouvelles alertes déclenchées.
    """
    triggered: List[Dict[str, Any]] = []

    async with get_async_session() as session:
        rules_result = await session.execute(select(AlertRule).where(AlertRule.enabled == True))  # noqa: E712
        rules = rules_result.scalars().all()

        for rule in rules:
            try:
                result = await _evaluate_rule(session, rule)
                if result:
                    triggered.append(result)
            except Exception as e:
                logger.error("[Alerting] Erreur évaluation règle %s: %s", rule.name, e)
                continue

        if triggered:
            await session.commit()

    return triggered


async def get_alert_summary() -> Dict[str, Any]:
    """Récupère un résumé rapide des alertes pour le dashboard.

    Returns:
        dict: résumé des alertes (actives non acquittées, dernières 24h, etc.)
    """
    async with get_async_session() as session:
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)

        # Non acquittées
        unack_result = await session.execute(select(func.count(AlertEvent.id)).where(AlertEvent.acknowledged == False))  # noqa: E712
        unacknowledged = unack_result.scalar() or 0

        # Dernières 24h
        recent_result = await session.execute(select(func.count(AlertEvent.id)).where(AlertEvent.created_at >= last_24h))
        recent_24h = recent_result.scalar() or 0

        # Critiques non acquittées
        critical_result = await session.execute(
            select(func.count(AlertEvent.id)).where(AlertEvent.acknowledged == False).where(AlertEvent.severity == "critical")  # noqa: E712
        )
        critical = critical_result.scalar() or 0

        # Règles actives
        rules_result = await session.execute(select(func.count(AlertRule.id)).where(AlertRule.enabled == True))  # noqa: E712
        active_rules = rules_result.scalar() or 0

        return {
            "unacknowledged": unacknowledged,
            "recent_24h": recent_24h,
            "critical": critical,
            "active_rules": active_rules,
        }


# ─────────────────────── Helpers ───────────────────────


def _serialize_rule(rule: AlertRule) -> Dict[str, Any]:
    return {
        "id": str(rule.id),
        "name": rule.name,
        "metric": rule.metric,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "window_minutes": rule.window_minutes,
        "service_filter": rule.service_filter,
        "notify_email": rule.notify_email,
        "enabled": rule.enabled,
        "cooldown_minutes": rule.cooldown_minutes,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def _serialize_event(event: AlertEvent) -> Dict[str, Any]:
    return {
        "id": str(event.id),
        "rule_id": str(event.rule_id) if event.rule_id else None,
        "rule_name": event.rule_name,
        "metric": event.metric,
        "current_value": event.current_value,
        "threshold": event.threshold,
        "severity": event.severity,
        "message": event.message,
        "acknowledged": event.acknowledged,
        "acknowledged_by": event.acknowledged_by,
        "acknowledged_at": event.acknowledged_at.isoformat() if event.acknowledged_at else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def _serialize_event_from_data(rule: AlertRule, value: float, severity: str, message: str) -> Dict[str, Any]:
    return {
        "rule_name": rule.name,
        "metric": rule.metric,
        "current_value": value,
        "threshold": rule.threshold,
        "severity": severity,
        "message": message,
    }


async def _is_in_cooldown(session, rule: AlertRule) -> bool:
    """Vérifie si la règle est en période de cooldown."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
    result = await session.execute(select(func.count(AlertEvent.id)).where(AlertEvent.rule_id == rule.id).where(AlertEvent.created_at >= cutoff))
    return (result.scalar() or 0) > 0


async def _compute_metric(session, rule: AlertRule) -> Optional[float]:
    """Calcule la valeur actuelle d'une métrique."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=rule.window_minutes)

    base = select(HttpRequest).where(HttpRequest.created_at >= cutoff)
    if rule.service_filter:
        base = base.where(HttpRequest.service_prefix == rule.service_filter)

    if rule.metric == "error_rate":
        # Taux d'erreurs (5xx)
        total_q = select(func.count(HttpRequest.id)).where(HttpRequest.created_at >= cutoff)
        error_q = select(func.count(HttpRequest.id)).where(
            HttpRequest.created_at >= cutoff,
            HttpRequest.status_code >= 500,
        )
        if rule.service_filter:
            total_q = total_q.where(HttpRequest.service_prefix == rule.service_filter)
            error_q = error_q.where(HttpRequest.service_prefix == rule.service_filter)

        total = (await session.execute(total_q)).scalar() or 0
        errors = (await session.execute(error_q)).scalar() or 0
        return (errors / total * 100) if total > 0 else 0.0

    elif rule.metric == "response_time":
        # Temps de réponse moyen
        avg_q = select(func.avg(HttpRequest.duration_ms)).where(HttpRequest.created_at >= cutoff)
        if rule.service_filter:
            avg_q = avg_q.where(HttpRequest.service_prefix == rule.service_filter)
        result = await session.execute(avg_q)
        return result.scalar()

    elif rule.metric == "error_count":
        # Nombre absolu d'erreurs
        error_q = select(func.count(HttpRequest.id)).where(
            HttpRequest.created_at >= cutoff,
            HttpRequest.status_code >= 500,
        )
        if rule.service_filter:
            error_q = error_q.where(HttpRequest.service_prefix == rule.service_filter)
        result = await session.execute(error_q)
        return float(result.scalar() or 0)

    elif rule.metric == "request_count":
        # Nombre de requêtes (peut servir à détecter une absence de trafic)
        count_q = select(func.count(HttpRequest.id)).where(HttpRequest.created_at >= cutoff)
        if rule.service_filter:
            count_q = count_q.where(HttpRequest.service_prefix == rule.service_filter)
        result = await session.execute(count_q)
        return float(result.scalar() or 0)

    return None


def _check_condition(value: float, condition: str, threshold: float) -> bool:
    """Vérifie si la condition de la règle est remplie."""
    checks = {
        "gt": value > threshold,
        "lt": value < threshold,
        "eq": abs(value - threshold) < 0.001,
        "gte": value >= threshold,
        "lte": value <= threshold,
    }
    return checks.get(condition, False)


def _build_message(rule: AlertRule, value: float) -> str:
    """Construit le message d'alerte."""
    condition_labels = {
        "gt": "supérieur à",
        "lt": "inférieur à",
        "eq": "égal à",
        "gte": "supérieur ou égal à",
        "lte": "inférieur ou égal à",
    }
    cond_label = condition_labels.get(rule.condition, rule.condition)
    service_part = f" (service: {rule.service_filter})" if rule.service_filter else ""

    metric_labels = {
        "error_rate": "Taux d'erreurs",
        "response_time": "Temps de réponse moyen",
        "error_count": "Nombre d'erreurs",
        "request_count": "Nombre de requêtes",
    }
    metric_label = metric_labels.get(rule.metric, rule.metric)

    units = {
        "error_rate": "%",
        "response_time": " ms",
        "error_count": "",
        "request_count": "",
    }
    unit = units.get(rule.metric, "")

    return (
        f"{metric_label} est {cond_label} {rule.threshold}{unit} "
        f"(valeur actuelle: {value:.1f}{unit}){service_part} "
        f"sur les {rule.window_minutes} dernières minutes."
    )
