"""Add tags and allowed_ips to api_keys.

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-09

Colonnes optionnelles :
- tags : JSONB array de chaînes (ex. ["production", "CI"])
- allowed_ips : JSONB array d'IP ou CIDR (ex. ["192.168.1.0/24", "10.0.0.1"])

Idempotent: skips if columns already exist.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0013"
down_revision: Optional[str] = "0012"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add tags and allowed_ips columns (idempotent)."""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("api_keys")]
    if "tags" not in columns:
        op.add_column(
            "api_keys",
            sa.Column(
                "tags",
                JSONB,
                nullable=True,
                comment="Tags optionnels (ex. production, CI)",
            ),
        )
    if "allowed_ips" not in columns:
        op.add_column(
            "api_keys",
            sa.Column(
                "allowed_ips",
                JSONB,
                nullable=True,
                comment="IP ou plages CIDR autorisées (vide ou null = toutes)",
            ),
        )


def downgrade() -> None:
    """Remove tags and allowed_ips columns."""
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS allowed_ips")
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS tags")
