"""Configuration de la base de données pour Admin Service.

Thin wrapper autour de ``common.async_database.AsyncDatabase``.
Les exports publics restent inchangés : ``Base``, ``init_db``,
``get_async_session``.
"""

from __future__ import annotations

import os

from common.async_database import AsyncDatabase

from app.config_loader import settings

_db = AsyncDatabase()

#: Base déclarative — importée par tous les modèles du service.
Base = _db.Base


async def init_db() -> None:
    """Initialise le moteur async, teste la connexion et lance Alembic."""
    cfg = settings()
    await _db.init(
        database_settings=cfg.database,
        models_import="app.models",
        alembic_ini=os.path.join(os.path.dirname(__file__), "..", "alembic.ini"),
    )


#: Context-manager retournant une session asynchrone.
#: Usage : ``async with get_async_session() as session: ...``
get_async_session = _db.get_session
