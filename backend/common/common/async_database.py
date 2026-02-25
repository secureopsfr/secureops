"""Module de base de données asynchrone réutilisable.

Fournit la classe ``AsyncDatabase`` qui encapsule la création du moteur
SQLAlchemy async, l'exécution des migrations Alembic et la gestion des
sessions.  Chaque service instancie sa propre ``AsyncDatabase`` afin
d'avoir un ``Base`` (et donc des métadonnées) isolé.

Usage typique dans ``app/db.py`` d'un service::

    from common.async_database import AsyncDatabase

    _db = AsyncDatabase()
    Base = _db.Base

    async def init_db() -> None:
        from app.config_loader import settings
        cfg = settings()
        await _db.init(
            database_settings=cfg.database,
            models_import="app.models",
            alembic_ini=os.path.join(os.path.dirname(__file__), "..", "alembic.ini"),
        )

    get_async_session = _db.get_session
"""

from __future__ import annotations

import importlib
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from common.config_base import DatabaseSettings
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)


def build_async_database_url() -> str:
    """Construit l'URL de connexion async à la base depuis ``DATABASE_URL``.

    Convertit automatiquement ``postgresql://`` en ``postgresql+asyncpg://``
    si nécessaire.

    Returns:
        str: chaîne de connexion pour le driver asyncpg.

    Raises:
        RuntimeError: si ``DATABASE_URL`` n'est pas définie.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if database_url.startswith("postgresql+asyncpg://"):
            return database_url
        return database_url

    raise RuntimeError(
        "La variable d'environnement DATABASE_URL n'est pas définie. " "Utilisez launch_dev.sh, docker-compose ou exportez-la manuellement."
    )


def run_alembic_migrations(alembic_ini: str) -> None:
    """Exécute les migrations Alembic en mode ``upgrade head``.

    Args:
        alembic_ini: chemin absolu ou relatif vers ``alembic.ini``.
    """
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(alembic_ini)
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations Alembic appliquées avec succès")
    except Exception as e:
        logger.error("Erreur lors de l'exécution des migrations Alembic: %s", e)
        raise


class AsyncDatabase:
    """Encapsule un moteur async SQLAlchemy, une session-factory et un ``Base``.

    Chaque micro-service instancie sa propre ``AsyncDatabase`` pour garder
    des métadonnées de modèles isolées.
    """

    def __init__(self) -> None:
        """Initialise la base de données."""
        self.Base = declarative_base()
        self.engine: AsyncEngine | None = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    async def init(
        self,
        database_settings: DatabaseSettings,
        *,
        models_import: str = "app.models",
        alembic_ini: str | None = None,
    ) -> None:
        """Initialise le moteur, teste la connexion et lance les migrations.

        Args:
            database_settings: paramètres de pool (``DatabaseSettings``).
            models_import: module Python à importer pour enregistrer les
                modèles dans ``Base.metadata`` (ex. ``"app.models"``).
            alembic_ini: chemin vers ``alembic.ini``.  Si ``None``, les
                migrations ne sont pas exécutées.

        Raises:
            RuntimeError: si la connexion échoue.
        """
        if self.engine is not None and self.session_maker is not None:
            logger.debug("Base de données déjà initialisée")
            return

        database_url = build_async_database_url()
        safe_url = database_url.split("@")[1] if "@" in database_url else "***"
        logger.info("Initialisation de la connexion à la base de données: %s", safe_url)

        try:
            self.engine = create_async_engine(
                database_url,
                echo=database_settings.echo,
                future=True,
                pool_pre_ping=database_settings.pool_pre_ping,
                pool_recycle=database_settings.pool_recycle,
                pool_timeout=database_settings.pool_timeout,
                connect_args=database_settings.connect_args or {},
            )
            self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

            # Test de connexion
            async with self.engine.begin() as conn:
                await conn.exec_driver_sql("SELECT 1")
            logger.info("Connexion à la base de données établie avec succès")

            # Importer les modèles pour enregistrer les métadonnées
            importlib.import_module(models_import)

            # Appliquer les migrations Alembic
            if alembic_ini is not None:
                run_alembic_migrations(alembic_ini)

            logger.info("Tables et migrations initialisées avec succès")
        except Exception as e:
            logger.error("Erreur lors de l'initialisation de la base de données: %s", e)
            self.engine = None
            self.session_maker = None
            raise RuntimeError(f"Impossible de se connecter à la base de données: {e}") from e

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Context-manager retournant une session asynchrone.

        Yields:
            AsyncSession: session ouverte.

        Raises:
            RuntimeError: si la base n'est pas initialisée.
        """
        if self.session_maker is None:
            raise RuntimeError("La session de base de données n'est pas initialisée")
        async with self.session_maker() as session:
            yield session
