"""Add result_mode column to scan_async_jobs.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-11
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: Optional[str] = "0001"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Add result_mode column (default 'single') to scan_async_jobs."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("scan_async_jobs")]
    if "result_mode" not in columns:
        op.add_column(
            "scan_async_jobs",
            sa.Column("result_mode", sa.String(length=20), nullable=False, server_default="single"),
        )


def downgrade() -> None:
    """Remove result_mode column from scan_async_jobs."""
    op.drop_column("scan_async_jobs", "result_mode")
