"""Service de gestion des emails de notification."""

import logging
from typing import Any, Dict

from app.db_sync import get_sync_session
from app.models.email import NotificationEmail
from app.services.email_campaign_common import (
    create_campaign_email,
    list_campaign_emails,
    schedule_campaign_email,
    send_campaign_email,
    update_campaign_email,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service de gestion des emails de notification."""

    def __init__(self):
        """Initialise le service."""
        pass

    async def create_notification_email(self, email_data) -> Dict[str, Any]:
        """
        Crée un nouvel email de notification.

        Args:
            email_data: Données de l'email de notification

        Returns:
            Dict contenant l'ID, le sujet de l'email créé et un message de confirmation
        """
        with get_sync_session() as db:
            try:
                return create_campaign_email(db, NotificationEmail, email_data, "Email de notification créé avec succès !")
            except Exception:
                db.rollback()
                raise

    async def get_notification_emails(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère la liste des emails de notification avec pagination.

        Args:
            limit: Nombre maximum d'emails
            offset: Nombre d'emails à ignorer

        Returns:
            Dictionnaire contenant les emails et les métadonnées de pagination
        """
        with get_sync_session() as db:
            return list_campaign_emails(db, NotificationEmail, limit, offset)

    async def send_notification_email(self, email_id: int) -> Dict[str, Any]:
        """Envoie un email de notification à tous les abonnés vérifiés.

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
                    model_cls=NotificationEmail,
                    email_id=email_id,
                    subscription_flag="new_features_notifications_enabled",
                    no_subscribers_message="Aucun abonné aux notifications trouvé",
                    logger=logger,
                )
            except Exception:
                db.rollback()
                raise

    def schedule_notification_email(self, email_id: int, scheduled_at: str) -> Dict[str, Any]:
        """
        Programme l'envoi d'un email de notification.

        Args:
            email_id: ID de l'email à programmer
            scheduled_at: Date et heure d'envoi programmé (format ISO)

        Returns:
            Informations de la programmation
        """
        with get_sync_session() as db:
            try:
                return schedule_campaign_email(db, NotificationEmail, email_id, scheduled_at)
            except Exception:
                db.rollback()
                raise

    async def update_notification_email(self, email_id: int, email_data) -> Dict[str, Any]:
        """
        Met à jour un email de notification.

        Args:
            email_id: ID de l'email à mettre à jour
            email_data: Nouvelles données de l'email de notification

        Returns:
            Dict contenant l'ID, le sujet de l'email mis à jour et un message de confirmation

        Raises:
            ValueError: Si l'email n'existe pas ou est déjà envoyé
        """
        with get_sync_session() as db:
            try:
                return update_campaign_email(db, NotificationEmail, email_id, email_data, "Email de notification mis à jour avec succès !")
            except Exception:
                db.rollback()
                raise
