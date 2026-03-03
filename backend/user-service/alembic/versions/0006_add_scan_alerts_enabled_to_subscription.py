"""Add scan_alerts_enabled to subscriptions — alertes scans planifiés.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-02

Colonne scan_alerts_enabled : si True, envoi d'emails pour régression score
ou finding critical sur les scans planifiés.

Idempotent : si la colonne existe déjà (créée par 0001 via create_all), on ne fait rien.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Optional[str] = "0005"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Ajoute la colonne scan_alerts_enabled à subscriptions (idempotent)."""
    bind = op.get_bind()
    cols = [c["name"] for c in inspect(bind).get_columns("subscriptions")]
    if "scan_alerts_enabled" in cols:
        return
    op.add_column(
        "subscriptions",
        sa.Column(
            "scan_alerts_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Alertes email pour régression score ou finding critical (scans planifiés)",
        ),
    )


def downgrade() -> None:
    """Supprime la colonne scan_alerts_enabled (idempotent)."""
    bind = op.get_bind()
    cols = [c["name"] for c in inspect(bind).get_columns("subscriptions")]
    if "scan_alerts_enabled" in cols:
        op.drop_column("subscriptions", "scan_alerts_enabled")
