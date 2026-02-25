"""Service de gestion des emails de notification."""

import secrets
from datetime import datetime, timezone
from typing import Any, Dict

from app.db_sync import get_sync_session
from app.email_config import send_newsletter_email
from app.models.email import NotificationEmail
from app.models.user import Subscription, User


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
                notification_email = NotificationEmail(
                    subject=email_data.subject,
                    content=email_data.content,
                    status="draft",
                    template_name=getattr(email_data, "template_name", None) or "newsletter.html",
                )

                db.add(notification_email)
                db.commit()
                db.refresh(notification_email)

                return {"id": notification_email.id, "subject": notification_email.subject, "message": "Email de notification créé avec succès !"}
            except Exception as e:
                db.rollback()
                raise e

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
            try:
                query = db.query(NotificationEmail)

                # Total avant pagination
                total = query.count()

                query = query.order_by(NotificationEmail.sent_at.desc())
                query = query.offset(offset).limit(limit)

                emails = query.all()

                from app.schemas.common import make_pagination_meta

                data = [
                    {
                        "id": email.id,
                        "subject": email.subject,
                        "content": email.content,
                        "sent_at": email.sent_at.isoformat(),
                        "recipients_count": email.recipients_count,
                        "status": email.status,
                        "scheduled_at": email.scheduled_at.isoformat() if email.scheduled_at else None,
                        "is_scheduled": email.is_scheduled,
                        "template_name": email.template_name or "newsletter.html",
                    }
                    for email in emails
                ]

                return {
                    "data": data,
                    **make_pagination_meta(total=total, limit=limit, offset=offset),
                }
            except Exception as e:
                raise e

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
                email = db.query(NotificationEmail).filter(NotificationEmail.id == email_id).first()
                if not email:
                    raise ValueError(f"Email avec l'ID {email_id} non trouvé")

                # Récupérer les utilisateurs avec new_features_notifications_enabled=True via la jointure avec subscriptions
                subscribers_query = (
                    db.query(User)
                    .join(Subscription, User.id == Subscription.user_id)
                    .filter(Subscription.new_features_notifications_enabled.is_(True))
                    .filter(User.email.isnot(None))
                )
                subscribers = subscribers_query.all()

                if not subscribers:
                    return {"message": "Aucun abonné aux notifications trouvé", "recipients_count": 0}

                sent_count = 0
                failed_count = 0

                template = email.template_name or "newsletter.html"

                for user in subscribers:
                    try:
                        # Utiliser l'email de l'utilisateur directement
                        unsubscribe_token = secrets.token_urlsafe(32)

                        await send_newsletter_email(
                            to_email=user.email,
                            subject=email.subject,
                            content=email.content,
                            unsubscribe_token=unsubscribe_token,
                            template_name=template,
                        )
                        sent_count += 1
                    except Exception as e:
                        print(f"Erreur lors de l'envoi à {user.email}: {str(e)}")
                        failed_count += 1

                if sent_count > 0:
                    email.status = "sent"
                    email.recipients_count = sent_count
                    email.sent_at = datetime.now(timezone.utc)
                else:
                    email.status = "failed"
                    email.recipients_count = 0

                db.commit()

                return {"message": f"Email envoyé à {sent_count} abonnés, {failed_count} échecs", "recipients_count": sent_count}

            except Exception as e:
                db.rollback()
                raise e

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
                email = db.query(NotificationEmail).filter(NotificationEmail.id == email_id).first()
                if not email:
                    raise ValueError(f"Email avec l'ID {email_id} non trouvé")

                if email.status == "sent":
                    raise ValueError("Cet email a déjà été envoyé")

                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))

                now = datetime.now(timezone.utc)
                if scheduled_datetime <= now:
                    raise ValueError("La date d'envoi doit être dans le futur")

                email.scheduled_at = scheduled_datetime
                email.is_scheduled = True
                email.status = "scheduled"

                db.commit()

                return {
                    "message": f"Email programmé pour le {scheduled_datetime.strftime('%d/%m/%Y à %H:%M')}",
                    "email_id": email_id,
                    "scheduled_at": scheduled_at,
                    "is_scheduled": True,
                }
            except Exception as e:
                db.rollback()
                raise e

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
                email = db.query(NotificationEmail).filter(NotificationEmail.id == email_id).first()
                if not email:
                    raise ValueError(f"Email avec l'ID {email_id} non trouvé")

                if email.status == "sent":
                    raise ValueError("Impossible de modifier un email déjà envoyé")

                email.subject = email_data.subject
                email.content = email_data.content
                if hasattr(email_data, "template_name") and email_data.template_name is not None:
                    email.template_name = email_data.template_name

                db.commit()
                db.refresh(email)

                return {"id": email.id, "subject": email.subject, "message": "Email de notification mis à jour avec succès !"}
            except Exception as e:
                db.rollback()
                raise e
