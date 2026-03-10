"""Add expires_at column to api_keys.

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-09

Colonne expires_at : date d'expiration optionnelle (null = pas d'expiration).
Par défaut les nouvelles clés expirent après 1 mois (30 jours).

Idempotent: skips if column already exists.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0012"
down_revision: Optional[str] = "0011"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add expires_at column to api_keys (idempotent)."""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("api_keys")]
    if "expires_at" in columns:
        return
    op.add_column(
        "api_keys",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Date d'expiration (null = jamais)",
        ),
    )


def downgrade() -> None:
    """Remove expires_at column from api_keys."""
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS expires_at")
