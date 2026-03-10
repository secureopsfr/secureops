"""Add api_keys table.

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-09

Table api_keys : clés API pour l'API publique (roadmap §1).
- id, user_id, key_hash, name, prefix, created_at, last_used_at
- Contrainte unique (user_id, name)
- Contrainte unique key_hash

Idempotent: skips creation if table already exists (e.g. from partial migration run).
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0011"
down_revision: Optional[str] = "0010"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Create api_keys table (idempotent)."""
    conn = op.get_bind()
    inspector = inspect(conn)
    if "api_keys" in inspector.get_table_names():
        # Table already exists (e.g. partial run), ensure indexes/constraint exist
        op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys (key_hash)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys (user_id)")
        op.execute("""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_api_keys_user_id_name'
              ) THEN
                ALTER TABLE api_keys ADD CONSTRAINT uq_api_keys_user_id_name
                  UNIQUE (user_id, name);
              END IF;
            END $$;
            """)
        return

    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            comment="UUID interne (clé primaire)",
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="Référence vers l'utilisateur",
        ),
        sa.Column(
            "key_hash",
            sa.String(64),
            nullable=False,
            comment="Hash SHA-256 de la clé (jamais stockée en clair)",
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="Nom de la clé (unique par utilisateur)",
        ),
        sa.Column(
            "prefix",
            sa.String(16),
            nullable=False,
            comment="Préfixe affiché (ex. sk_...) pour identification sans exposer la clé",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Date de création",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Dernière utilisation de la clé",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_unique_constraint("uq_api_keys_user_id_name", "api_keys", ["user_id", "name"])


def downgrade() -> None:
    """Drop api_keys table (idempotent)."""
    op.execute("DROP TABLE IF EXISTS api_keys")
