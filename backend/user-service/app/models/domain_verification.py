"""Modèles pour la preuve de propriété DNS (domaine vérifié + challenges en attente)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class DomainVerification(Base):
    """Domaine vérifié par TXT DNS pour un utilisateur (eTLD+1 normalisé)."""

    __tablename__ = "domain_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String(255), nullable=False, unique=True)
    verified_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class DomainVerificationChallenge(Base):
    """Challenge en attente : token hashé jusqu'à vérification DNS réussie."""

    __tablename__ = "domain_verification_challenges"
    __table_args__ = (UniqueConstraint("user_id", "domain", name="uq_domain_verification_challenges_user_domain"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String(255), nullable=False)
    token_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
