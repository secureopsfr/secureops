"""Configuration Alembic pour admin-service.

Ce module configure l'environnement Alembic pour gérer les migrations
de la base de données du admin-service. Il combine les métadonnées
des deux bases déclaratives (Base et AppBase).
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import MetaData, engine_from_config, pool

from alembic import context

# Ajouter le répertoire parent au PYTHONPATH pour les imports app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configuration Alembic
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Construit l'URL de connexion synchrone depuis l'environnement.

    Alembic utilise un driver synchrone (psycopg2), donc on convertit
    postgresql+asyncpg:// en postgresql:// si nécessaire.
    """
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if not url:
        raise RuntimeError("DATABASE_URL n'est pas définie. " "Exportez-la avant de lancer les migrations Alembic.")
    return url


def get_combined_metadata() -> MetaData:
    """Combine les métadonnées de Base (async) et AppBase (sync).

    Le admin-service utilise deux bases déclaratives :
    - Base (db.py) : AnalyticsEvent, HttpRequest, AuditLog, AlertRule, AlertEvent
    - AppBase (base_model.py) : ContactMessage, User, Subscription, NewsletterEmail, NotificationEmail

    Pour qu'Alembic autogenerate puisse détecter les changements sur
    toutes les tables, on fusionne les deux MetaData en un seul.
    """
    # Importer les modèles pour enregistrer les tables sur leurs métadonnées
    # Importer tous les modèles pour déclencher l'enregistrement
    import app.models  # noqa: F401
    from app.db import Base  # noqa: F401
    from app.models.base_model import AppBase  # noqa: F401
    from app.models.base_model import ContactMessage  # noqa: F401
    from app.models.email import NewsletterEmail, NotificationEmail  # noqa: F401
    from app.models.user import Subscription, User  # noqa: F401

    # Fusionner les deux metadata
    combined = MetaData()
    for table in Base.metadata.sorted_tables:
        table.to_metadata(combined)
    for table in AppBase.metadata.sorted_tables:
        table.to_metadata(combined)

    return combined


target_metadata = get_combined_metadata()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (génère le SQL sans connexion)."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="admin_alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (avec connexion à la base)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="admin_alembic_version",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
