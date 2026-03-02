#!/usr/bin/env python3
"""
Script de nettoyage périodique de l'historique des scans.

Supprime les scans plus anciens que la durée configurée par chaque utilisateur.
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
    """Exécute le nettoyage pour tous les utilisateurs."""
    url = get_async_url()
    engine = create_async_engine(url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Subscription).where(Subscription.history_retention != "none"))
        subscriptions = result.scalars().all()
        total_deleted = 0

        for sub in subscriptions:
            try:
                days = int(sub.history_retention)
            except (ValueError, TypeError):
                continue
            cutoff = datetime.now(UTC) - timedelta(days=days)
            stmt = delete(Scan).where(Scan.user_id == sub.user_id, Scan.created_at < cutoff)
            r = await session.execute(stmt)
            deleted = r.rowcount or 0
            if deleted > 0:
                total_deleted += deleted
                logger.info("User %s: %s scans supprimés (rétention %s jours)", sub.user_id, deleted, days)

        await session.commit()
        logger.info("Nettoyage terminé: %s scans supprimés au total", total_deleted)


def main() -> None:
    """Point d'entrée."""
    try:
        asyncio.run(run_cleanup())
    except Exception as e:
        logger.exception("Erreur lors du nettoyage: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
