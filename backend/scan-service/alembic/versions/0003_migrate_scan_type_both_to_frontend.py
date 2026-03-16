"""Migrate scan_type 'both' to 'frontend' in scan_async_jobs.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-16

Upgrade: UPDATE scan_async_jobs SET scan_type = 'frontend' WHERE scan_type = 'both'
Downgrade: no-op (data not reverted)
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: Optional[str] = "0002"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Migrate both -> frontend in scan_async_jobs."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "scan_async_jobs" not in inspector.get_table_names():
        return
    op.execute(sa.text("UPDATE scan_async_jobs SET scan_type = 'frontend' WHERE scan_type = 'both'"))


def downgrade() -> None:
    """No data rollback (both no longer supported)."""
    pass
