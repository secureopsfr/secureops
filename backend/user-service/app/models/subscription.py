"""Modèle SQLAlchemy pour la table subscriptions."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Subscription(Base):
    """Modèle représentant un abonnement utilisateur dans la base de données."""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence vers l'utilisateur",
    )

    plan = Column(String(50), nullable=False, default="free", comment="Plan d'abonnement (free / premium)")

    status = Column(String(50), nullable=False, default="active", comment="Statut de l'abonnement (active / canceled / trial)")

    stripe_customer_id = Column(String(255), nullable=True, index=True, comment="Identifiant Stripe du client")

    current_period_end = Column(DateTime(timezone=True), nullable=True, comment="Date de fin de la période courante")

    newsletter_enabled = Column(Boolean, nullable=False, default=False, comment="Inscription à la newsletter")

    new_features_notifications_enabled = Column(
        Boolean, nullable=False, default=False, comment="Notifications par mail pour nouvelles données ou features"
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, comment="Date de création")

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        comment="Date de mise à jour",
    )

    user = relationship("User", back_populates="subscription")

    def __repr__(self) -> str:
        """Représentation string de l'abonnement."""
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan}, "
            f"status={self.status}, stripe_customer_id={self.stripe_customer_id})>"
        )
