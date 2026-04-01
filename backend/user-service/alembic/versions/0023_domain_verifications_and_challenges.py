"""Domain verifications (DNS TXT) and pending challenges.

Revision ID: 0023
Revises: 0022
Create Date: 2026-03-31
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0023"
down_revision: Optional[str] = "0022"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Create domain_verifications and domain_verification_challenges tables."""
    op.create_table(
        "domain_verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("domain", name="uq_domain_verifications_domain"),
    )
    op.create_index("ix_domain_verifications_user_id", "domain_verifications", ["user_id"])
    op.create_index(
        "ix_domain_verifications_user_domain",
        "domain_verifications",
        ["user_id", "domain"],
    )

    op.create_table(
        "domain_verification_challenges",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "domain", name="uq_domain_verification_challenges_user_domain"),
    )
    op.create_index("ix_domain_verification_challenges_expires_at", "domain_verification_challenges", ["expires_at"])


def downgrade() -> None:
    """Drop domain verification tables and indexes."""
    op.drop_index("ix_domain_verification_challenges_expires_at", table_name="domain_verification_challenges")
    op.drop_table("domain_verification_challenges")
    op.drop_index("ix_domain_verifications_user_domain", table_name="domain_verifications")
    op.drop_index("ix_domain_verifications_user_id", table_name="domain_verifications")
    op.drop_table("domain_verifications")
