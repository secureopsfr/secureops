"""Modèles pour les utilisateurs et abonnements."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import de AppBase (même base déclarative pour partager la même session de base de données)
from app.models.base_model import AppBase


class User(AppBase):
    """Modèle représentant un utilisateur dans la base de données.

    Attributes:
        id (UUID): identifiant unique de l'utilisateur.
        cognito_sub (str): identifiant Cognito (sub) de l'utilisateur.
        email (str): adresse email de l'utilisateur.
        created_at (datetime): date de création dans la base de données.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    cognito_sub = Column(String(255), unique=True, nullable=False, index=True, comment="Cognito sub (clé principale logique, unique)")

    email = Column(String(255), nullable=False, index=True, comment="Email de l'utilisateur")

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, comment="Date de création dans la base de données"
    )

    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("cognito_sub", name="uq_users_cognito_sub"),)

    def __repr__(self) -> str:
        """Représentation string de l'utilisateur."""
        return f"<User(id={self.id}, cognito_sub={self.cognito_sub}, email={self.email})>"


class Subscription(AppBase):
    """Modèle représentant un abonnement utilisateur dans la base de données.

    Attributes:
        id (UUID): identifiant unique de l'abonnement.
        user_id (UUID): référence vers l'utilisateur.
        plan (str): plan d'abonnement (free / premium).
        status (str): statut de l'abonnement (active / canceled / trial).
        stripe_customer_id (str): identifiant Stripe du client.
        current_period_end (datetime): date de fin de la période courante.
        newsletter_enabled (bool): inscription à la newsletter.
        new_features_notifications_enabled (bool): notifications par mail pour nouvelles données ou features.
        created_at (datetime): date de création.
        updated_at (datetime): date de mise à jour.
    """

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
            f"status={self.status}, newsletter_enabled={self.newsletter_enabled})>"
        )
