"""Add alert config columns to scheduled_scans.

Revision ID: 0022
Revises: 0021
Create Date: 2026-03-31

Idempotent: ADD COLUMN IF NOT EXISTS — évite DuplicateColumn si la base
CI ou locale a déjà les colonnes (init SQL, migration rejouée, etc.).
"""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add alert-related columns to scheduled_scans."""
    op.execute(
        """
        ALTER TABLE scheduled_scans
        ADD COLUMN IF NOT EXISTS alert_on_regression BOOLEAN NOT NULL DEFAULT true
        """
    )
    op.execute(
        """
        ALTER TABLE scheduled_scans
        ADD COLUMN IF NOT EXISTS alert_on_critical_finding BOOLEAN NOT NULL DEFAULT true
        """
    )
    op.execute(
        """
        ALTER TABLE scheduled_scans
        ADD COLUMN IF NOT EXISTS alert_score_threshold INTEGER NULL
        """
    )


def downgrade() -> None:
    """Drop alert-related columns from scheduled_scans."""
    op.execute("ALTER TABLE scheduled_scans DROP COLUMN IF EXISTS alert_score_threshold")
    op.execute("ALTER TABLE scheduled_scans DROP COLUMN IF EXISTS alert_on_critical_finding")
    op.execute("ALTER TABLE scheduled_scans DROP COLUMN IF EXISTS alert_on_regression")
