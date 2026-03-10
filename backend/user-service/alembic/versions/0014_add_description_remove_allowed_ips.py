"""Add description and remove allowed_ips from api_keys.

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-09

- description : VARCHAR(500) optionnel
- Remove allowed_ips
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0014"
down_revision: Optional[str] = "0013"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add description column, remove allowed_ips."""
    op.add_column(
        "api_keys",
        sa.Column(
            "description",
            sa.String(500),
            nullable=True,
            comment="Description optionnelle de la clé",
        ),
    )
    op.drop_column("api_keys", "allowed_ips")


def downgrade() -> None:
    """Remove description, restore allowed_ips."""
    op.drop_column("api_keys", "description")
    op.add_column(
        "api_keys",
        sa.Column(
            "allowed_ips",
            JSONB,
            nullable=True,
            comment="IP ou plages CIDR autorisées (vide ou null = toutes)",
        ),
    )
