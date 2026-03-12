"""Modèles de base pour l'application."""

import enum

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# Base pour les modèles (synchrone)
AppBase = declarative_base()


# ========== Enums ==========


class StatusEnum(str, enum.Enum):
    """Énumération des statuts des messages de contact."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PROCESSED = "processed"


# ========== Models ==========


class ContactMessage(AppBase):
    """Modèle pour les messages de contact.

    Attributes:
        id (int): identifiant unique du message.
        first_name (str): prénom de l'expéditeur.
        last_name (str): nom de l'expéditeur.
        email (str): adresse email de l'expéditeur.
        subject (str): sujet du message.
        message (str): contenu du message.
        status (str): statut du message.
        created_at (datetime): date d'envoi du message.
        updated_at (datetime): date de dernière modification.
    """

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    message = Column(String(5000), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        """Représentation string du message de contact."""
        return f"<ContactMessage(id={self.id}, email='{self.email}', subject='{self.subject}', status='{self.status}')>"
