"""Add daily_quotas table.

Revision ID: 0021
Revises: 0020
Create Date: 2026-03-19

Crée la table daily_quotas pour le suivi du quota journalier
(scans + crawls cumulés) par utilisateur (identifié par cognito_sub).
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021"
down_revision: Optional[str] = "0020"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée la table daily_quotas."""
    op.create_table(
        "daily_quotas",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("cognito_sub", sa.String(255), nullable=False),
        sa.Column("date_utc", sa.Date(), nullable=False),
        sa.Column("jobs_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("cognito_sub", "date_utc", name="uq_daily_quotas_sub_date"),
    )
    op.create_index("ix_daily_quotas_cognito_sub_date", "daily_quotas", ["cognito_sub", "date_utc"])


def downgrade() -> None:
    """Supprime la table daily_quotas."""
    op.drop_index("ix_daily_quotas_cognito_sub_date", table_name="daily_quotas")
    op.drop_table("daily_quotas")
