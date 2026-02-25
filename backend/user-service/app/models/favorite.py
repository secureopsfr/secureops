"""Modèle SQLAlchemy pour la table favorites."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Favorite(Base):
    """Modèle représentant un favori de recherche utilisateur dans la base de données."""

    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence vers l'utilisateur",
    )

    search_type = Column(String(100), nullable=False, index=True, comment="Type de recherche")

    query_json = Column(JSONB, nullable=False, comment="Données JSON de la requête")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True, comment="Date de création")

    user = relationship("User", back_populates="favorites")

    def __repr__(self) -> str:
        """Représentation string du favori."""
        return f"<Favorite(id={self.id}, user_id={self.user_id}, search_type={self.search_type}, " f"created_at={self.created_at})>"
