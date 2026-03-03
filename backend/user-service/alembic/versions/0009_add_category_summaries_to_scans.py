"""Add category_summaries_json to scans — résumés par catégorie (checks_count, etc.).

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-03

Colonne category_summaries_json (JSONB, nullable) pour stocker les résumés
par catégorie incluant checks_count. Les scans existants restent compatibles.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Optional[str] = "0008"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Ajoute la colonne category_summaries_json à scans (idempotent)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "scans" not in inspector.get_table_names():
        return
    cols = [c["name"] for c in inspector.get_columns("scans")]
    if "category_summaries_json" in cols:
        return
    op.add_column(
        "scans",
        sa.Column(
            "category_summaries_json",
            JSONB,
            nullable=True,
            comment="Résumés par catégorie (checks_count, label, etc.)",
        ),
    )


def downgrade() -> None:
    """Supprime la colonne category_summaries_json (idempotent)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "scans" not in inspector.get_table_names():
        return
    cols = [c["name"] for c in inspector.get_columns("scans")]
    if "category_summaries_json" not in cols:
        return
    op.drop_column("scans", "category_summaries_json")
