"""Service pour le journal d'audit des actions admin.

Fournit des fonctions pour :
- Enregistrer une action admin (log_action)
- Consulter l'historique des actions (get_audit_logs)
- Obtenir des statistiques d'audit (get_audit_stats)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from common.logging_config import mask_email
from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_async_session
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    admin_email: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Enregistre une action admin dans le journal d'audit.

    Args:
        admin_email: email de l'administrateur.
        action: type d'action (ex: user.ban, contact.status_change).
        entity_type: type d'entité concernée.
        entity_id: identifiant de l'entité.
        details: détails supplémentaires (ancien/nouveau statut, etc.).
        ip_address: adresse IP de l'admin.
    """
    try:
        async with get_async_session() as session:
            entry = AuditLog(
                admin_email=admin_email,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
            )
            session.add(entry)
            await session.commit()
            logger.info("[Audit] %s -> %s on %s:%s", mask_email(admin_email), action, entity_type, entity_id)
    except SQLAlchemyError as e:
        logger.error("[Audit] Erreur lors de l'enregistrement: %s", e)
        # Ne pas propager l'erreur pour ne pas bloquer l'action principale


async def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    admin_email: Optional[str] = None,
    entity_id: Optional[str] = None,
    window_minutes: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Récupère l'historique des actions admin.

    Args:
        entity_type: filtrer par type d'entité.
        action: filtrer par type d'action.
        admin_email: filtrer par admin.
        entity_id: filtrer par entité.
        window_minutes: fenêtre temporelle en minutes.
        limit: nombre max de résultats.
        offset: décalage pour pagination.

    Returns:
        dict: {logs: [...], total: int}
    """
    async with get_async_session() as session:
        base_query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        if entity_type:
            base_query = base_query.where(AuditLog.entity_type == entity_type)
            count_query = count_query.where(AuditLog.entity_type == entity_type)
        if action:
            base_query = base_query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if admin_email:
            base_query = base_query.where(AuditLog.admin_email.ilike(f"%{admin_email}%"))
            count_query = count_query.where(AuditLog.admin_email.ilike(f"%{admin_email}%"))
        if entity_id:
            base_query = base_query.where(AuditLog.entity_id == entity_id)
            count_query = count_query.where(AuditLog.entity_id == entity_id)
        if window_minutes:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            base_query = base_query.where(AuditLog.created_at >= cutoff)
            count_query = count_query.where(AuditLog.created_at >= cutoff)

        # Total
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Logs paginés
        stmt = base_query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        result = await session.execute(stmt)
        logs = result.scalars().all()

        from app.schemas.common import make_pagination_meta

        return {
            "logs": [
                {
                    "id": str(log.id),
                    "admin_email": log.admin_email,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            **make_pagination_meta(total=total, limit=limit, offset=offset),
        }


async def get_audit_stats(window_minutes: Optional[int] = None) -> Dict[str, Any]:
    """Récupère des statistiques d'audit.

    Args:
        window_minutes: fenêtre temporelle.

    Returns:
        dict: statistiques agrégées.
    """
    async with get_async_session() as session:
        cutoff = None
        if window_minutes:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        # Total d'actions
        total_query = select(func.count(AuditLog.id))
        if cutoff:
            total_query = total_query.where(AuditLog.created_at >= cutoff)
        total_result = await session.execute(total_query)
        total = total_result.scalar() or 0

        # Actions par type
        by_action_query = (
            select(AuditLog.action, func.count(AuditLog.id).label("count")).group_by(AuditLog.action).order_by(desc(func.count(AuditLog.id)))
        )
        if cutoff:
            by_action_query = by_action_query.where(AuditLog.created_at >= cutoff)
        by_action_result = await session.execute(by_action_query)
        by_action = {row.action: row.count for row in by_action_result}

        # Actions par entité
        by_entity_query = (
            select(AuditLog.entity_type, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.entity_type)
            .order_by(desc(func.count(AuditLog.id)))
        )
        if cutoff:
            by_entity_query = by_entity_query.where(AuditLog.created_at >= cutoff)
        by_entity_result = await session.execute(by_entity_query)
        by_entity = {row.entity_type: row.count for row in by_entity_result}

        # Admins les plus actifs
        by_admin_query = (
            select(AuditLog.admin_email, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.admin_email)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(10)
        )
        if cutoff:
            by_admin_query = by_admin_query.where(AuditLog.created_at >= cutoff)
        by_admin_result = await session.execute(by_admin_query)
        by_admin = [{"email": row.admin_email, "count": row.count} for row in by_admin_result]

        return {
            "total_actions": total,
            "by_action": by_action,
            "by_entity": by_entity,
            "top_admins": by_admin,
        }
