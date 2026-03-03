"""Add scan_alert_events table — historique des alertes déclenchées.

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-03

Table scan_alert_events : url, scheduled_scan_id, alert_type, email_sent, triggered_at.

Idempotent : si la table existe déjà (créée par 0001 via create_all), on ne fait rien.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Optional[str] = "0007"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée la table scan_alert_events (idempotent)."""
    bind = op.get_bind()
    if "scan_alert_events" in inspect(bind).get_table_names():
        return
    op.create_table(
        "scan_alert_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "scheduled_scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scheduled_scans.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Supprime la table scan_alert_events (idempotent)."""
    bind = op.get_bind()
    if "scan_alert_events" in inspect(bind).get_table_names():
        op.drop_table("scan_alert_events")
