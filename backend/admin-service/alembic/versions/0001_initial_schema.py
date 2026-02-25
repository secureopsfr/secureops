"""Initial schema — création de toutes les tables admin-service.

Revision ID: 0001
Revises: None
Create Date: 2026-02-17

Cette migration crée le schéma initial complet du admin-service.
Elle utilise create_all(checkfirst=True) pour être idempotente :
- Sur une base VIDE : crée toutes les tables.
- Sur une base EXISTANTE : ne fait rien (les tables existent déjà).

Pour les bases existantes (avant Alembic), exécuter :
    alembic stamp head
Cela marque la base comme étant à jour sans exécuter la migration.
"""

from typing import Optional, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Optional[str] = None
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée toutes les tables du admin-service."""
    bind = op.get_bind()

    # Importer tous les modèles pour enregistrer les tables
    import app.models  # noqa: F401
    from app.db import Base
    from app.models.base_model import AppBase, ContactMessage  # noqa: F401
    from app.models.email import NewsletterEmail, NotificationEmail  # noqa: F401
    from app.models.user import Subscription, User  # noqa: F401

    # Créer les tables (checkfirst=True = idempotent)
    Base.metadata.create_all(bind=bind, checkfirst=True)
    AppBase.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Supprime toutes les tables du admin-service (ordre inverse pour les FK)."""
    tables = [
        "alert_events",
        "alert_rules",
        "audit_logs",
        "http_requests",
        "analytics_events",
        "notification_emails",
        "newsletter_emails",
        "subscriptions",
        "contact_messages",
        "users",
    ]
    for table_name in tables:
        op.drop_table(table_name)
