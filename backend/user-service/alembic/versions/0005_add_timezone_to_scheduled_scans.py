"""Add timezone to scheduled_scans — heure locale utilisateur (ex. Europe/Paris).

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-02

Colonne timezone : fuseau de l'utilisateur pour interpréter schedule_hour/minute.
Ex. Europe/Paris. Si null/UTC, comportement inchangé (heure UTC).
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Optional[str] = "0004"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Ajoute la colonne timezone à scheduled_scans."""
    op.add_column(
        "scheduled_scans",
        sa.Column(
            "timezone",
            sa.String(64),
            nullable=True,
            comment="Fuseau utilisateur (ex. Europe/Paris) pour schedule_hour/minute",
        ),
    )


def downgrade() -> None:
    """Supprime la colonne timezone."""
    op.drop_column("scheduled_scans", "timezone")
