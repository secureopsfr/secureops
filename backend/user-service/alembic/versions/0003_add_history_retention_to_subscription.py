"""Add history_retention to subscriptions.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-02

Colonne history_retention : durée de conservation de l'historique des scans.
Valeurs : none, 7, 30, 90, 365 (jours). Défaut : 30.
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
    """Ajoute la colonne history_retention à subscriptions."""
    op.add_column(
        "subscriptions",
        sa.Column(
            "history_retention",
            sa.String(10),
            nullable=False,
            server_default="30",
            comment="Durée de conservation de l'historique (none, 7, 30, 90, 365 jours)",
        ),
    )


def downgrade() -> None:
    """Supprime la colonne history_retention."""
    op.drop_column("subscriptions", "history_retention")
