"""Add scan_async_jobs table.

Revision ID: 0001
Revises:
Create Date: 2026-03-11
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: Optional[str] = None
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Create scan_async_jobs table if not exists."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "scan_async_jobs" in inspector.get_table_names():
        return

    op.create_table(
        "scan_async_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("scan_type", sa.String(length=20), nullable=False, server_default="frontend"),
        sa.Column("input_json", JSONB, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("result_json", JSONB, nullable=True),
        sa.Column("error_json", JSONB, nullable=True),
        sa.Column("progress_log_json", JSONB, nullable=False),
        sa.Column("last_step", sa.String(length=128), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("job_token_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scan_async_jobs_user_id", "scan_async_jobs", ["user_id"])
    op.create_index("ix_scan_async_jobs_status", "scan_async_jobs", ["status"])
    op.create_index("ix_scan_async_jobs_next_retry_at", "scan_async_jobs", ["next_retry_at"])
    op.create_index("ix_scan_async_jobs_created_at", "scan_async_jobs", ["created_at"])
    op.create_index("ix_scan_async_jobs_expires_at", "scan_async_jobs", ["expires_at"])


def downgrade() -> None:
    """Drop scan_async_jobs table."""
    op.drop_table("scan_async_jobs")
