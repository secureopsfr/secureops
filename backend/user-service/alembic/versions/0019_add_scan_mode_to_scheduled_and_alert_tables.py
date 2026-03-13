"""Add scan_mode to scheduled_scans and scan_alert_events.

Revision ID: 0019
Revises: 0018
Create Date: 2026-03-13

Upgrade:
- ajoute scheduled_scans.scan_mode (VARCHAR, default passive)
- ajoute scan_alert_events.scan_mode (VARCHAR, default passive)
- backfill des lignes existantes NULL/vides vers passive
- ajoute des CHECK sur scan_mode

Downgrade:
- supprime les CHECK
- supprime les colonnes scan_mode
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: Optional[str] = "0018"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None

_ALLOWED_EXPR = "scan_mode IN ('passive', 'intrusive', 'destructive', 'custom')"

_TABLES = [
    ("scheduled_scans", "ck_scheduled_scans_scan_mode_allowed"),
    ("scan_alert_events", "ck_scan_alert_events_scan_mode_allowed"),
]


def _table_has_column(conn: sa.Connection, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    if table_name not in inspector.get_table_names():
        return False
    cols = {c["name"] for c in inspector.get_columns(table_name)}
    return column_name in cols


def _has_check_constraint(conn: sa.Connection, table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(conn)
    if table_name not in inspector.get_table_names():
        return False
    checks = inspector.get_check_constraints(table_name)
    return any((c.get("name") or "") == constraint_name for c in checks)


def upgrade() -> None:
    """Add scan_mode column and CHECK constraints to scheduled/alerts tables."""
    conn = op.get_bind()

    for table_name, check_name in _TABLES:
        if not _table_has_column(conn, table_name, "scan_mode"):
            op.add_column(
                table_name,
                sa.Column(
                    "scan_mode",
                    sa.String(length=20),
                    nullable=False,
                    server_default="passive",
                    comment="Mode de scan : passive, intrusive, destructive, custom",
                ),
            )

        op.execute(sa.text(f"UPDATE {table_name} SET scan_mode = 'passive' WHERE scan_mode IS NULL OR scan_mode = ''"))

        if not _has_check_constraint(conn, table_name, check_name):
            op.create_check_constraint(check_name, table_name, _ALLOWED_EXPR)


def downgrade() -> None:
    """Drop CHECK constraints and scan_mode columns from scheduled/alerts tables."""
    conn = op.get_bind()

    for table_name, check_name in _TABLES:
        if _has_check_constraint(conn, table_name, check_name):
            op.drop_constraint(check_name, table_name, type_="check")
        if _table_has_column(conn, table_name, "scan_mode"):
            op.drop_column(table_name, "scan_mode")
