#!/usr/bin/env python3
"""
Script de nettoyage périodique de l'historique des scans et des alertes.

Supprime les scans et les événements d'alerte plus anciens que la durée configurée
par chaque utilisateur (history_retention).
À exécuter via cron (ex. quotidiennement).

Usage:
    cd backend/user-service && . venv/bin/activate && python scripts/cleanup_scan_history.py

Variables d'environnement:
    DATABASE_URL: URL de connexion PostgreSQL (postgresql://... ou postgresql+asyncpg://...)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime, timedelta

# Ajouter le répertoire parent au path pour importer app (avant imports locaux)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402, F401 — enregistre les modèles
from app.models.scan import Scan  # noqa: E402
from app.models.scan_alert_event import ScanAlertEvent  # noqa: E402
from app.models.subscription import Subscription  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_async_url() -> str:
    """Convertit DATABASE_URL en URL asyncpg si nécessaire."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL non définie")
    if url.startswith("postgresql://") and "asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def run_cleanup() -> None:
    """Exécute le nettoyage pour tous les utilisateurs (scans + historique des alertes)."""
    url = get_async_url()
    engine = create_async_engine(url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Subscription).where(Subscription.history_retention != "none"))
        subscriptions = result.scalars().all()
        total_scans_deleted = 0
        total_alerts_deleted = 0

        for sub in subscriptions:
            try:
                days = int(sub.history_retention)
            except (ValueError, TypeError):
                continue
            cutoff = datetime.now(UTC) - timedelta(days=days)

            # Supprimer les scans plus anciens que la rétention
            stmt_scans = delete(Scan).where(Scan.user_id == sub.user_id, Scan.created_at < cutoff)
            r_scans = await session.execute(stmt_scans)
            deleted_scans = r_scans.rowcount or 0
            if deleted_scans > 0:
                total_scans_deleted += deleted_scans
                logger.info("User %s: %s scans supprimés (rétention %s jours)", sub.user_id, deleted_scans, days)

            # Supprimer les événements d'alerte plus anciens que la rétention
            stmt_alerts = delete(ScanAlertEvent).where(
                ScanAlertEvent.user_id == sub.user_id,
                ScanAlertEvent.triggered_at < cutoff,
            )
            r_alerts = await session.execute(stmt_alerts)
            deleted_alerts = r_alerts.rowcount or 0
            if deleted_alerts > 0:
                total_alerts_deleted += deleted_alerts
                logger.info("User %s: %s alertes supprimées (rétention %s jours)", sub.user_id, deleted_alerts, days)

        await session.commit()
        logger.info("Nettoyage terminé: %s scans et %s alertes supprimés au total", total_scans_deleted, total_alerts_deleted)


def main() -> None:
    """Point d'entrée."""
    try:
        asyncio.run(run_cleanup())
    except Exception as e:
        logger.exception("Erreur lors du nettoyage: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
