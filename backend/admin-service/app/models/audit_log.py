"""Modèle de stockage du journal d'audit des actions admin.

Ce module définit la table pour stocker toutes les actions effectuées
par les administrateurs (changement de statut, envoi de newsletter, ban, etc.)
afin de fournir un historique complet et traçable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class AuditLog(Base):
    """Représente une entrée du journal d'audit.

    Attributes:
        id (UUID): identifiant unique de l'entrée.
        admin_email (str): email de l'administrateur qui a effectué l'action.
        action (str): type d'action (ex: user.ban, contact.status_change, newsletter.send).
        entity_type (str): type d'entité concernée (user, contact, newsletter, notification, subscription).
        entity_id (str | None): identifiant de l'entité concernée.
        details (dict | None): détails supplémentaires en JSON (ancien/nouveau statut, etc.).
        ip_address (str | None): adresse IP de l'administrateur (pseudonymisée).
        created_at (datetime): horodatage de l'action en UTC.
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    admin_email = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(255), nullable=True, index=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self) -> str:  # pragma: no cover
        """Retourne une représentation concise utile pour le debug."""
        return (
            f"AuditLog(admin={self.admin_email!r}, action={self.action!r}, "
            f"entity={self.entity_type!r}:{self.entity_id!r}, created_at={self.created_at})"
        )
