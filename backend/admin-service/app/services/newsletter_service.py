"""Service de gestion des emails newsletter."""

import logging
from typing import Any, Dict

from app.db_sync import get_sync_session
from app.models.email import NewsletterEmail
from app.services.email_campaign_common import (
    create_campaign_email,
    list_campaign_emails,
    schedule_campaign_email,
    send_campaign_email,
    update_campaign_email,
)

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service de gestion des emails newsletter."""

    def __init__(self):
        """Initialise le service."""
        pass

    async def create_newsletter_email(self, email_data) -> Dict[str, Any]:
        """
        Crée un nouvel email newsletter.

        Args:
            email_data: Données de l'email newsletter

        Returns:
            Dict contenant l'ID, le sujet de l'email créé et un message de confirmation
        """
        with get_sync_session() as db:
            try:
                return create_campaign_email(db, NewsletterEmail, email_data, "Email newsletter créé avec succès !")
            except Exception:
                db.rollback()
                raise

    async def get_newsletter_emails(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère la liste des emails newsletter avec pagination.

        Args:
            limit: Nombre maximum d'emails
            offset: Nombre d'emails à ignorer

        Returns:
            Dictionnaire contenant les emails et les métadonnées de pagination
        """
        with get_sync_session() as db:
            return list_campaign_emails(db, NewsletterEmail, limit, offset)

    async def send_newsletter_email(self, email_id: int) -> Dict[str, Any]:
        """Envoie un email newsletter à tous les abonnés vérifiés.

        Args:
            email_id: ID de l'email à envoyer

        Returns:
            Résultat de l'envoi avec le nombre de destinataires

        Raises:
            ValueError: Si l'email n'existe pas
        """
        with get_sync_session() as db:
            try:
                return await send_campaign_email(
                    db=db,
                    model_cls=NewsletterEmail,
                    email_id=email_id,
                    subscription_flag="newsletter_enabled",
                    no_subscribers_message="Aucun abonné à la newsletter trouvé",
                    logger=logger,
                )
            except Exception:
                db.rollback()
                raise

    def schedule_newsletter_email(self, email_id: int, scheduled_at: str) -> Dict[str, Any]:
        """
        Programme l'envoi d'un email newsletter.

        Args:
            email_id: ID de l'email à programmer
            scheduled_at: Date et heure d'envoi programmé (format ISO)

        Returns:
            Informations de la programmation
        """
        with get_sync_session() as db:
            try:
                return schedule_campaign_email(db, NewsletterEmail, email_id, scheduled_at)
            except Exception:
                db.rollback()
                raise

    async def update_newsletter_email(self, email_id: int, email_data) -> Dict[str, Any]:
        """
        Met à jour un email newsletter.

        Args:
            email_id: ID de l'email à mettre à jour
            email_data: Nouvelles données de l'email newsletter

        Returns:
            Dict contenant l'ID, le sujet de l'email mis à jour et un message de confirmation

        Raises:
            ValueError: Si l'email n'existe pas ou est déjà envoyé
        """
        with get_sync_session() as db:
            try:
                return update_campaign_email(db, NewsletterEmail, email_id, email_data, "Email newsletter mis à jour avec succès !")
            except Exception:
                db.rollback()
                raise
