"""Move scan_alerts_enabled from subscriptions to scheduled_scans.

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-02

- Ajoute scan_alerts_enabled à scheduled_scans (par scan, défaut True).
- Supprime scan_alerts_enabled de subscriptions.

Idempotent : si la colonne existe déjà (créée par 0001 via create_all), on ne fait rien.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Optional[str] = "0006"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Ajoute scan_alerts_enabled à scheduled_scans, supprime de subscriptions (idempotent)."""
    bind = op.get_bind()
    insp = inspect(bind)
    if "scheduled_scans" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("scheduled_scans")]
        if "scan_alerts_enabled" not in cols:
            op.add_column(
                "scheduled_scans",
                sa.Column(
                    "scan_alerts_enabled",
                    sa.Boolean(),
                    nullable=False,
                    server_default="true",
                    comment="Alertes email pour régression score ou finding critical (ce scan)",
                ),
            )
    if "subscriptions" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("subscriptions")]
        if "scan_alerts_enabled" in cols:
            op.drop_column("subscriptions", "scan_alerts_enabled")


def downgrade() -> None:
    """Inverse : scan_alerts_enabled sur subscriptions, supprime de scheduled_scans (idempotent)."""
    bind = op.get_bind()
    insp = inspect(bind)
    if "subscriptions" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("subscriptions")]
        if "scan_alerts_enabled" not in cols:
            op.add_column(
                "subscriptions",
                sa.Column(
                    "scan_alerts_enabled",
                    sa.Boolean(),
                    nullable=False,
                    server_default="true",
                    comment="Alertes email pour régression score ou finding critical (scans planifiés)",
                ),
            )
    if "scheduled_scans" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("scheduled_scans")]
        if "scan_alerts_enabled" in cols:
            op.drop_column("scheduled_scans", "scan_alerts_enabled")
