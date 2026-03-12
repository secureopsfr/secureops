"""Modèle SQLAlchemy pour la table api_keys."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class ApiKey(Base):
    """Modèle représentant une clé API utilisateur.

    Stocke uniquement le hash de la clé (SHA-256) pour des raisons de sécurité.
    Le préfixe (ex. sk_...) est conservé pour l'affichage dans la liste.
    """

    __tablename__ = "api_keys"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="UUID interne (clé primaire)",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence vers l'utilisateur",
    )

    key_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="Hash SHA-256 de la clé (jamais stockée en clair)",
    )

    name = Column(
        String(100),
        nullable=False,
        comment="Nom de la clé (unique par utilisateur)",
    )

    prefix = Column(
        String(16),
        nullable=False,
        comment="Préfixe affiché (ex. sk_...) pour identification sans exposer la clé",
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="Date de création",
    )

    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière utilisation de la clé",
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration (null = pas d'expiration)",
    )

    tags = Column(
        JSONB,
        nullable=True,
        comment="Tags optionnels (ex. production, CI)",
    )

    description = Column(
        String(500),
        nullable=True,
        comment="Description optionnelle de la clé",
    )

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_api_keys_user_id_name"),)

    def __repr__(self) -> str:
        """Représentation string du modèle pour debug."""
        return f"<ApiKey(id={self.id}, user_id={self.user_id}, name={self.name!r})>"
