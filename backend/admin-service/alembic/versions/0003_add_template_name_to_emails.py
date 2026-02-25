"""Ajout de la colonne template_name aux tables newsletter_emails et notification_emails.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-18

Permet de stocker le nom du template HTML utilisé pour l'envoi de chaque email.
La valeur par défaut est 'newsletter.html' pour rétrocompatibilité.
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Optional[str] = "0002"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Ajoute la colonne template_name aux tables d'emails (idempotent)."""
    conn = op.get_bind()
    for table in ("newsletter_emails", "notification_emails"):
        # Ne pas échouer si la colonne existe déjà (ré-exécution des migrations)
        result = conn.execute(
            sa.text("SELECT 1 FROM information_schema.columns " "WHERE table_name = :t AND column_name = 'template_name'"),
            {"t": table},
        )
        if result.scalar() is None:
            op.add_column(
                table,
                sa.Column(
                    "template_name",
                    sa.String(100),
                    nullable=True,
                    server_default="newsletter.html",
                ),
            )


def downgrade() -> None:
    """Supprime la colonne template_name des tables d'emails."""
    op.drop_column("notification_emails", "template_name")
    op.drop_column("newsletter_emails", "template_name")
