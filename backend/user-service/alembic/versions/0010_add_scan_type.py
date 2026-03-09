"""Add scan_type to scans, scheduled_scans and scan_alert_events.

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-09

Colonne scan_type (VARCHAR) : frontend, backend, custom.
- scans : défaut 'frontend' pour rétrocompatibilité
- scheduled_scans : défaut 'frontend'
- scan_alert_events : défaut 'frontend'
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: Optional[str] = "0009"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # scans
    if "scans" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scans")]
        if "scan_type" not in cols:
            op.add_column(
                "scans",
                sa.Column(
                    "scan_type",
                    sa.String(20),
                    nullable=False,
                    server_default="frontend",
                    comment="Type de scan : frontend, backend, custom",
                ),
            )

    # scheduled_scans
    if "scheduled_scans" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scheduled_scans")]
        if "scan_type" not in cols:
            op.add_column(
                "scheduled_scans",
                sa.Column(
                    "scan_type",
                    sa.String(20),
                    nullable=False,
                    server_default="frontend",
                    comment="Type de scan : frontend, backend, custom",
                ),
            )

    # scan_alert_events
    if "scan_alert_events" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scan_alert_events")]
        if "scan_type" not in cols:
            op.add_column(
                "scan_alert_events",
                sa.Column(
                    "scan_type",
                    sa.String(20),
                    nullable=False,
                    server_default="frontend",
                    comment="Type de scan : frontend, backend, custom",
                ),
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "scans" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scans")]
        if "scan_type" in cols:
            op.drop_column("scans", "scan_type")

    if "scheduled_scans" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scheduled_scans")]
        if "scan_type" in cols:
            op.drop_column("scheduled_scans", "scan_type")

    if "scan_alert_events" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("scan_alert_events")]
        if "scan_type" in cols:
            op.drop_column("scan_alert_events", "scan_type")
