"""Configuration de la base de données synchrone.

Ce module instancie le moteur synchrone SQLAlchemy pour les services
qui utilisent des sessions synchrones.

Les migrations sont gérées par Alembic (voir alembic/ à la racine du service).
"""

import logging
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config_loader import settings

logger = logging.getLogger(__name__)

# Moteur et session factory synchrones
sync_engine = None
SyncSessionLocal: sessionmaker[Session] | None = None


def _build_sync_database_url() -> str:
    """Construit l'URL de connexion synchrone à la base.

    Returns:
        str: chaîne de connexion complète (driver psycopg2).
    """
    # PRIORITÉ 1: Utiliser la configuration depuis settings (qui a déjà template_db)
    try:
        cfg = settings()
        database_url = cfg.general.database_url
        # S'assurer que c'est postgresql:// (pas postgresql+asyncpg://)
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        # S'assurer qu'on utilise template_db
        if "/admin_db" in database_url:
            database_url = database_url.replace("/admin_db", "/template_db")
        logger.info("[db_sync] Utilisation de la config depuis settings: %s", database_url.split("@")[1] if "@" in database_url else "***")
        return database_url
    except Exception as e:
        logger.warning("[db_sync] Erreur lors du chargement de la config, fallback: %s", e)

    # PRIORITÉ 2: Utiliser DATABASE_URL depuis l'environnement
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # S'assurer que c'est postgresql:// (pas postgresql+asyncpg://)
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        # S'assurer qu'on utilise template_db
        if "/admin_db" in database_url:
            database_url = database_url.replace("/admin_db", "/template_db")
        logger.info("[db_sync] Utilisation de DATABASE_URL depuis l'environnement: %s", database_url.split("@")[1] if "@" in database_url else "***")
        return database_url

    # Aucun fallback avec credentials en dur — DATABASE_URL est obligatoire.
    raise RuntimeError(
        "La variable d'environnement DATABASE_URL n'est pas définie et la config est absente. "
        "Utilisez launch_dev.sh, docker-compose ou exportez-la manuellement."
    )


def init_sync_db() -> None:
    """Initialise le moteur synchrone.

    Les tables sont créées/migrées par Alembic (appelé dans init_db).
    Ce module se contente d'initialiser le moteur et de tester la connexion.

    Raises:
        RuntimeError: si l'initialisation échoue.
    """
    global sync_engine, SyncSessionLocal

    if sync_engine is not None and SyncSessionLocal is not None:
        logger.debug("Base de données synchrone déjà initialisée")
        return

    database_url = _build_sync_database_url()
    db_info = database_url.split("@")[1] if "@" in database_url else "***"
    logger.info("Initialisation de la connexion synchrone à la base de données: %s", db_info)
    # NB: Ne jamais logger l'URL complète (contient le mot de passe)

    try:
        sync_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
        SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

        # Test de connexion
        from sqlalchemy import text

        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Connexion synchrone à la base de données établie avec succès")
    except Exception as e:
        logger.error("Erreur lors de l'initialisation de la base de données synchrone: %s", e)
        sync_engine = None
        SyncSessionLocal = None
        raise RuntimeError(f"Impossible de se connecter à la base de données synchrone: {e}") from e


@contextmanager
def get_sync_session() -> Iterator[Session]:
    """Context manager retournant une session synchrone.

    Yields:
        Session: session ouverte.

    Raises:
        RuntimeError: si la base n'est pas initialisée.
    """
    if SyncSessionLocal is None:
        raise RuntimeError("La session de base de données synchrone n'est pas initialisée")
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
