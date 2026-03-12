"""Add multi-scan fields to scheduled_scans.

Revision ID: 0016
Revises: 0015
Create Date: 2026-03-12
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016"
down_revision: Optional[str] = "0015"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add result_mode and urls_json to scheduled_scans table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "scheduled_scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("scheduled_scans")}

    if "result_mode" not in cols:
        op.add_column(
            "scheduled_scans",
            sa.Column(
                "result_mode",
                sa.String(length=10),
                nullable=False,
                server_default="single",
                comment="Mode de résultat : single ou multi",
            ),
        )

    if "urls_json" not in cols:
        op.add_column(
            "scheduled_scans",
            sa.Column(
                "urls_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Liste des URLs pour un scan planifié multi-pages",
            ),
        )


def downgrade() -> None:
    """Remove result_mode and urls_json from scheduled_scans table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "scheduled_scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("scheduled_scans")}

    if "urls_json" in cols:
        op.drop_column("scheduled_scans", "urls_json")
    if "result_mode" in cols:
        op.drop_column("scheduled_scans", "result_mode")
