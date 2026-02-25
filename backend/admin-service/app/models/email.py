"""Modèles pour les emails (newsletter et notifications)."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

# Import de AppBase (même base déclarative pour partager la même session de base de données)
from app.models.base_model import AppBase


class NewsletterEmail(AppBase):
    """Modèle pour les emails de newsletter envoyés.

    Attributes:
        id (int): identifiant unique de l'email.
        subject (str): sujet de l'email.
        content (str): contenu HTML de l'email.
        sent_at (datetime): date d'envoi de l'email.
        recipients_count (int): nombre de destinataires.
        status (str): statut de l'envoi (sent, failed, draft).
        scheduled_at (datetime): date et heure d'envoi programmé.
        is_scheduled (bool): indique si l'email est programmé.
        template_name (str): nom du template HTML utilisé pour l'envoi.
    """

    __tablename__ = "newsletter_emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    recipients_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="draft", nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_scheduled = Column(Boolean, default=False, nullable=False)
    template_name = Column(String(100), default="newsletter.html", nullable=True)

    def __repr__(self):
        """Représentation string de l'email newsletter."""
        return f"<NewsletterEmail(id={self.id}, subject='{self.subject}', status='{self.status}')>"


class NotificationEmail(AppBase):
    """Modèle pour les emails de notification envoyés.

    Attributes:
        id (int): identifiant unique de l'email.
        subject (str): sujet de l'email.
        content (str): contenu HTML de l'email.
        sent_at (datetime): date d'envoi de l'email.
        recipients_count (int): nombre de destinataires.
        status (str): statut de l'envoi (sent, failed, draft).
        scheduled_at (datetime): date et heure d'envoi programmé.
        is_scheduled (bool): indique si l'email est programmé.
        template_name (str): nom du template HTML utilisé pour l'envoi.
    """

    __tablename__ = "notification_emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    recipients_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="draft", nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_scheduled = Column(Boolean, default=False, nullable=False)
    template_name = Column(String(100), default="newsletter.html", nullable=True)

    def __repr__(self):
        """Représentation string de l'email de notification."""
        return f"<NotificationEmail(id={self.id}, subject='{self.subject}', status='{self.status}')>"
