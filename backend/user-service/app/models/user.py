"""Modèle SQLAlchemy pour la table users."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    """Modèle représentant un utilisateur dans la base de données.

    Cette table est créée de manière lazy au premier appel API authentifié.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    cognito_sub = Column(String(255), unique=True, nullable=False, index=True, comment="Cognito sub (clé principale logique, unique)")

    email = Column(String(255), nullable=False, index=True, comment="Email de l'utilisateur")

    dark_mode = Column(Boolean, nullable=False, default=True, comment="Préférence de thème : True = dark, False = light")

    language = Column(String(5), nullable=False, default="fr", comment="Langue préférée : fr = français, en = anglais")

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, comment="Date de création dans la base de données"
    )

    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")

    scheduled_scans = relationship("ScheduledScan", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("cognito_sub", name="uq_users_cognito_sub"),)

    def __repr__(self) -> str:
        """Représentation string de l'utilisateur."""
        return f"<User(id={self.id}, cognito_sub={self.cognito_sub}, email={self.email})>"
