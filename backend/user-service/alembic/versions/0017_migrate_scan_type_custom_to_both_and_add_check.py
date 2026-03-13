"""Migrate scan_type custom->both and enforce allowed values.

Revision ID: 0017
Revises: 0016
Create Date: 2026-03-13

Applique sur les tables user-service:
- scans
- scheduled_scans
- scan_alert_events

Upgrade:
- migration de donnees: scan_type='custom' -> 'both'
- ajout d'une contrainte CHECK pour limiter scan_type a frontend|backend|both

Downgrade:
- suppression des contraintes CHECK
- migration inverse: scan_type='both' -> 'custom'
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: Optional[str] = "0016"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


_TABLES: tuple[str, ...] = ("scans", "scheduled_scans", "scan_alert_events")
_CHECKS: dict[str, str] = {
    "scans": "ck_scans_scan_type_allowed",
    "scheduled_scans": "ck_scheduled_scans_scan_type_allowed",
    "scan_alert_events": "ck_scan_alert_events_scan_type_allowed",
}
_ALLOWED_EXPR = "scan_type IN ('frontend', 'backend', 'both')"


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
    """Migrate data and add strict CHECK constraints for scan_type."""
    conn = op.get_bind()

    for table in _TABLES:
        if not _table_has_column(conn, table, "scan_type"):
            continue
        op.execute(sa.text(f"UPDATE {table} SET scan_type = 'both' WHERE scan_type = 'custom'"))

    for table, check_name in _CHECKS.items():
        if not _table_has_column(conn, table, "scan_type"):
            continue
        if _has_check_constraint(conn, table, check_name):
            continue
        op.create_check_constraint(
            check_name,
            table,
            _ALLOWED_EXPR,
        )


def downgrade() -> None:
    """Drop CHECK constraints and migrate data back (both -> custom)."""
    conn = op.get_bind()

    for table, check_name in _CHECKS.items():
        if not _table_has_column(conn, table, "scan_type"):
            continue
        if _has_check_constraint(conn, table, check_name):
            op.drop_constraint(check_name, table, type_="check")

    for table in _TABLES:
        if not _table_has_column(conn, table, "scan_type"):
            continue
        op.execute(sa.text(f"UPDATE {table} SET scan_type = 'custom' WHERE scan_type = 'both'"))
