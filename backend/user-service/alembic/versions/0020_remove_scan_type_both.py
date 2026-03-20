"""Remove scan_type 'both' and restrict to frontend|backend only.

Revision ID: 0020
Revises: 0019
Create Date: 2026-03-16

Upgrade:
- migration de donnees: scan_type='both' -> 'frontend'
- drop des contraintes CHECK actuelles (frontend|backend|both)
- ajout de nouvelles contraintes CHECK: frontend|backend uniquement

Downgrade:
- drop des nouvelles contraintes
- migration both -> frontend reste (pas de retour arrière pour both)
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020"
down_revision: Optional[str] = "0019"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


_TABLES: tuple[str, ...] = ("scans", "scheduled_scans", "scan_alert_events")
_CHECKS: dict[str, str] = {
    "scans": "ck_scans_scan_type_allowed",
    "scheduled_scans": "ck_scheduled_scans_scan_type_allowed",
    "scan_alert_events": "ck_scan_alert_events_scan_type_allowed",
}
_NEW_ALLOWED_EXPR = "scan_type IN ('frontend', 'backend')"


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
    """Migrate both->frontend, replace CHECK constraints."""
    conn = op.get_bind()

    for table in _TABLES:
        if not _table_has_column(conn, table, "scan_type"):
            continue
        op.execute(sa.text(f"UPDATE {table} SET scan_type = 'frontend' WHERE scan_type = 'both'"))

    for table, check_name in _CHECKS.items():
        if not _table_has_column(conn, table, "scan_type"):
            continue
        if _has_check_constraint(conn, table, check_name):
            op.drop_constraint(check_name, table, type_="check")
        op.create_check_constraint(
            check_name,
            table,
            _NEW_ALLOWED_EXPR,
        )


def downgrade() -> None:
    """Restore previous CHECK (frontend|backend|both). No data rollback for both."""
    conn = op.get_bind()
    old_expr = "scan_type IN ('frontend', 'backend', 'both')"

    for table, check_name in _CHECKS.items():
        if not _table_has_column(conn, table, "scan_type"):
            continue
        if _has_check_constraint(conn, table, check_name):
            op.drop_constraint(check_name, table, type_="check")
        op.create_check_constraint(check_name, table, old_expr)
