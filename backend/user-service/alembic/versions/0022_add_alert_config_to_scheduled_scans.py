"""Add alert config columns to scheduled_scans.

Revision ID: 0022
Revises: 0021
Create Date: 2026-03-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scheduled_scans",
        sa.Column(
            "alert_on_regression",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Envoyer une alerte en cas de régression du score",
        ),
    )
    op.add_column(
        "scheduled_scans",
        sa.Column(
            "alert_on_critical_finding",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Envoyer une alerte en cas de finding critique",
        ),
    )
    op.add_column(
        "scheduled_scans",
        sa.Column(
            "alert_score_threshold",
            sa.Integer(),
            nullable=True,
            comment="Seuil de régression pour l'alerte (pts). NULL = valeur par défaut du serveur (10 pts)",
        ),
    )


def downgrade() -> None:
    op.drop_column("scheduled_scans", "alert_score_threshold")
    op.drop_column("scheduled_scans", "alert_on_critical_finding")
    op.drop_column("scheduled_scans", "alert_on_regression")
