"""Add scan_mode to scans and enforce allowed values.

Revision ID: 0018
Revises: 0017
Create Date: 2026-03-13

Upgrade:
- ajoute la colonne scans.scan_mode (VARCHAR, default passive)
- backfill des lignes existantes NULL/vides vers passive
- ajoute un CHECK sur scan_mode

Downgrade:
- supprime le CHECK
- supprime la colonne scan_mode
"""

from typing import Optional, Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: Optional[str] = "0017"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None

_TABLE = "scans"
_COLUMN = "scan_mode"
_CHECK_NAME = "ck_scans_scan_mode_allowed"
_ALLOWED_EXPR = "scan_mode IN ('passive', 'intrusive', 'destructive', 'custom')"


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
    """Add scan_mode column and CHECK constraint to scans."""
    conn = op.get_bind()

    if not _table_has_column(conn, _TABLE, _COLUMN):
        op.add_column(
            _TABLE,
            sa.Column(
                _COLUMN,
                sa.String(length=20),
                nullable=False,
                server_default="passive",
                comment="Mode de scan : passive, intrusive, destructive, custom",
            ),
        )

    op.execute(sa.text("UPDATE scans SET scan_mode = 'passive' WHERE scan_mode IS NULL OR scan_mode = ''"))

    if not _has_check_constraint(conn, _TABLE, _CHECK_NAME):
        op.create_check_constraint(
            _CHECK_NAME,
            _TABLE,
            _ALLOWED_EXPR,
        )


def downgrade() -> None:
    """Drop CHECK and column scan_mode from scans."""
    conn = op.get_bind()

    if _has_check_constraint(conn, _TABLE, _CHECK_NAME):
        op.drop_constraint(_CHECK_NAME, _TABLE, type_="check")

    if _table_has_column(conn, _TABLE, _COLUMN):
        op.drop_column(_TABLE, _COLUMN)
