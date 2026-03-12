"""Add multi-scan fields to scans history table.

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-12
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: Optional[str] = "0014"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add result_mode, page_results_json and urls_json to scans."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("scans")}

    if "result_mode" not in cols:
        op.add_column(
            "scans",
            sa.Column(
                "result_mode",
                sa.String(length=10),
                nullable=False,
                server_default="single",
                comment="Mode du résultat : single ou multi",
            ),
        )

    if "page_results_json" not in cols:
        op.add_column(
            "scans",
            sa.Column(
                "page_results_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Résultats par page pour un scan multi-URL",
            ),
        )

    if "urls_json" not in cols:
        op.add_column(
            "scans",
            sa.Column(
                "urls_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Liste des URLs scannées pour un scan multi-URL",
            ),
        )


def downgrade() -> None:
    """Remove multi-scan fields from scans."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "scans" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("scans")}

    if "urls_json" in cols:
        op.drop_column("scans", "urls_json")
    if "page_results_json" in cols:
        op.drop_column("scans", "page_results_json")
    if "result_mode" in cols:
        op.drop_column("scans", "result_mode")
