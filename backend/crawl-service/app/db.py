"""Configuration base de données pour crawl-service."""

from __future__ import annotations

import os

from common.async_database import AsyncDatabase

from app.config_loader import settings

_db = AsyncDatabase()
Base = _db.Base


async def init_db() -> bool:
    """Initialise la base et crée les tables crawl.

    Returns:
        bool: True si DB prête, sinon False.
    """
    if not os.getenv("DATABASE_URL"):
        return False
    cfg = settings()
    await _db.init(
        database_settings=cfg.database,
        models_import="app.persistence.models",
        alembic_ini=os.path.join(os.path.dirname(__file__), "..", "alembic.ini"),
    )
    return True


get_async_session = _db.get_session
