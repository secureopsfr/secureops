"""Add scans table — historique des scans de posture sécurité.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-02

Table scans : id, user_id (FK users.id), url, status, score, findings_json,
timestamp, duration, created_at.
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Optional[str] = "0001"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée la table scans (idempotent : skip si déjà créée par 0001.create_all)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "scans" in inspector.get_table_names():
        return
    op.create_table(
        "scans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="Référence vers l'utilisateur",
        ),
        sa.Column("url", sa.String(2048), nullable=False, comment="URL scannée"),
        sa.Column("status", sa.String(50), nullable=False, server_default="success", comment="Statut du scan"),
        sa.Column("score", sa.Integer(), nullable=True, comment="Note /100"),
        sa.Column("findings_json", JSONB, nullable=False, comment="Findings normalisés"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, comment="Horodatage du scan"),
        sa.Column("duration", sa.Float(), nullable=False, comment="Durée en secondes"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
            comment="Date de création",
        ),
    )


def downgrade() -> None:
    """Supprime la table scans."""
    op.drop_table("scans")
