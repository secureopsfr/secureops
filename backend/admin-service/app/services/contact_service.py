"""Service de gestion des messages de contact."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from common.logging_config import mask_email

from app.db_sync import get_sync_session
from app.email_config import SENDER_EMAIL, _load_template, _send_graph_email
from app.models.base_model import ContactMessage

logger = logging.getLogger(__name__)


class ContactService:
    """Service de gestion des messages de contact (méthodes admin uniquement)."""

    def __init__(self):
        """Initialise le service."""
        pass

    async def get_contact_messages(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère la liste des messages de contact avec pagination.

        Args:
            status: Filtrer par statut
            limit: Nombre maximum de messages
            offset: Nombre de messages à ignorer

        Returns:
            Dictionnaire contenant les messages et les métadonnées de pagination
        """
        with get_sync_session() as db:
            try:
                query = db.query(ContactMessage)

                if status:
                    query = query.filter(ContactMessage.status == status)

                # Total avant pagination
                total = query.count()

                query = query.order_by(ContactMessage.created_at.desc())
                query = query.offset(offset).limit(limit)

                messages = query.all()

                from app.schemas.common import make_pagination_meta

                data = [
                    {
                        "id": msg.id,
                        "first_name": msg.first_name,
                        "last_name": msg.last_name,
                        "email": msg.email,
                        "subject": msg.subject,
                        "message": msg.message,
                        "status": msg.status,
                        "created_at": msg.created_at.isoformat(),
                        "updated_at": msg.updated_at.isoformat(),
                    }
                    for msg in messages
                ]

                return {
                    "data": data,
                    **make_pagination_meta(total=total, limit=limit, offset=offset),
                }
            except Exception as e:
                raise e

    async def update_contact_message_status(self, message_id: int, new_status: str) -> Dict[str, Any]:
        """
        Met à jour le statut d'un message de contact.

        Args:
            message_id: ID du message
            new_status: Nouveau statut

        Returns:
            Message mis à jour
        """
        with get_sync_session() as db:
            try:
                message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()

                if not message:
                    raise ValueError(f"Message avec l'ID {message_id} non trouvé")

                message.status = new_status
                db.commit()
                db.refresh(message)

                return {
                    "id": message.id,
                    "first_name": message.first_name,
                    "last_name": message.last_name,
                    "email": message.email,
                    "subject": message.subject,
                    "message": message.message,
                    "status": message.status,
                    "created_at": message.created_at.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                }
            except Exception as e:
                db.rollback()
                raise e

    async def delete_contact_message(self, message_id: int) -> Dict[str, Any]:
        """
        Supprime un message de contact.

        Args:
            message_id: ID du message à supprimer

        Returns:
            Confirmation de la suppression
        """
        with get_sync_session() as db:
            try:
                message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()

                if not message:
                    raise ValueError(f"Message avec l'ID {message_id} non trouvé")

                db.delete(message)
                db.commit()

                return {"message": f"Message {message_id} supprimé avec succès"}
            except ValueError:
                raise
            except Exception as e:
                db.rollback()
                raise e

    async def reply_to_contact(self, message_id: int, reply_body: str) -> Dict[str, Any]:
        """
        Répond à un message de contact par email et met à jour son statut.

        Args:
            message_id: ID du message auquel répondre
            reply_body: Contenu HTML de la réponse

        Returns:
            Confirmation de l'envoi
        """
        with get_sync_session() as db:
            try:
                message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()

                if not message:
                    raise ValueError(f"Message avec l'ID {message_id} non trouvé")

                contact_name = f"{message.first_name} {message.last_name}"

                # Charger le template de réponse
                html_content = _load_template(
                    "contact_reply.html",
                    {
                        "contact_name": contact_name,
                        "reply_content": reply_body,
                        "original_subject": message.subject,
                        "original_message": message.message,
                    },
                )

                subject = f"Re: {message.subject}"

                # Envoyer l'email
                _send_graph_email(
                    to_email=message.email,
                    subject=subject,
                    html_body=html_content,
                    from_address=SENDER_EMAIL,
                )

                # Mettre à jour le statut du message
                message.status = "processed"
                message.updated_at = datetime.now(timezone.utc)
                db.commit()

                logger.info("Réponse envoyée à %s pour le message %s", mask_email(message.email), message_id)

                return {
                    "message": f"Réponse envoyée avec succès à {message.email}",
                    "email": message.email,
                    "subject": subject,
                }
            except ValueError:
                raise
            except Exception as e:
                db.rollback()
                logger.error("Erreur lors de l'envoi de la réponse au message %s: %s", message_id, e)
                raise

    async def create_contact_message(self, contact_data) -> Dict[str, Any]:
        """
        Crée un nouveau message de contact.

        Args:
            contact_data: Données du message de contact

        Returns:
            Dict contenant l'ID du message créé et un message de confirmation
        """
        with get_sync_session() as db:
            try:
                contact_message = ContactMessage(
                    first_name=contact_data.first_name,
                    last_name=contact_data.last_name,
                    email=contact_data.email,
                    subject=contact_data.subject,
                    message=contact_data.message,
                )

                db.add(contact_message)
                db.commit()
                db.refresh(contact_message)

                return {
                    "id": contact_message.id,
                    "message": (
                        "Message envoyé avec succès ! Un email de confirmation vous a été envoyé. " "Nous vous répondrons dans les plus brefs délais."
                    ),
                }
            except Exception as e:
                db.rollback()
                raise e
