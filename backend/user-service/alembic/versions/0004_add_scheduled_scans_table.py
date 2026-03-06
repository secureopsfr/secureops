"""Add scheduled_scans table — scans planifiés (monitoring continu).

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-02

Table scheduled_scans : id, user_id, url, frequency, schedule_hour, schedule_minute,
schedule_day_of_week, schedule_day_of_month, next_run_at, enabled, created_at, updated_at.

Idempotent : si la table existe déjà (créée par 0001 via create_all), on ne fait rien.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Optional[str] = "0003"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée la table scheduled_scans (idempotent)."""
    bind = op.get_bind()
    if "scheduled_scans" in inspect(bind).get_table_names():
        return
    op.create_table(
        "scheduled_scans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Référence vers l'utilisateur",
        ),
        sa.Column("url", sa.String(2048), nullable=False, comment="URL à scanner"),
        sa.Column("frequency", sa.String(20), nullable=False, comment="Fréquence : daily, weekly, monthly"),
        sa.Column("schedule_hour", sa.Integer(), nullable=False, server_default="2", comment="Heure d'exécution (0-23)"),
        sa.Column("schedule_minute", sa.Integer(), nullable=False, server_default="0", comment="Minute d'exécution (0-59)"),
        sa.Column("schedule_day_of_week", sa.Integer(), nullable=True, comment="Jour semaine pour weekly (0=lundi, 6=dimanche)"),
        sa.Column("schedule_day_of_month", sa.Integer(), nullable=True, comment="Jour du mois pour monthly (1-31)"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False, index=True, comment="Prochaine exécution planifiée"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true", comment="Scan actif ou en pause"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Date de création"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Dernière modification"),
    )


def downgrade() -> None:
    """Supprime la table scheduled_scans (idempotent)."""
    bind = op.get_bind()
    if "scheduled_scans" in inspect(bind).get_table_names():
        op.drop_table("scheduled_scans")
