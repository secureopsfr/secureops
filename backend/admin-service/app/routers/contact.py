"""Router pour les routes admin des messages de contact."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.common import ContactMessageResponse, ContactMessageUpdateRequest, ErrorResponse
from app.services.audit_service import log_action
from app.services.contact_service import ContactService


class ContactReplyRequest(BaseModel):
    """Schéma de requête pour répondre à un message de contact."""

    body: str


# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_50 = Query(50)
DEFAULT_QUERY_0 = Query(0)
DEFAULT_QUERY_NONE = Query(None)

router = APIRouter()

# Instance du service
contact_service = ContactService()


@router.get("/contact", responses={500: {"model": ErrorResponse}})
async def get_contact_messages(
    status: Optional[str] = DEFAULT_QUERY_NONE, limit: int = DEFAULT_QUERY_50, offset: int = DEFAULT_QUERY_0
) -> Dict[str, Any]:
    """
    Récupère la liste des messages de contact avec pagination (admin uniquement).

    Args:
        status: Filtrer par statut (pending, in_progress, processed)
        limit: Nombre maximum de messages à retourner
        offset: Nombre de messages à ignorer

    Returns:
        dict: {data: [...], total, page, per_page, total_pages}

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        result = await contact_service.get_contact_messages(status=status, limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.put("/contact/{message_id}", response_model=ContactMessageResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def update_contact_message_status(message_id: int, update_data: ContactMessageUpdateRequest) -> Dict[str, Any]:
    """
    Met à jour le statut d'un message de contact (admin uniquement).

    Args:
        message_id: ID du message à mettre à jour
        update_data: Données de mise à jour contenant le nouveau statut

    Returns:
        ContactMessageResponse: Message de contact mis à jour

    Raises:
        HTTPException: Erreur 404 si message non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await contact_service.update_contact_message_status(message_id, update_data.status)
        await log_action(
            admin_email="admin",
            action="contact.status_change",
            entity_type="contact",
            entity_id=str(message_id),
            details={"new_status": update_data.status},
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.delete("/contact/{message_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def delete_contact_message(message_id: int) -> Dict[str, Any]:
    """
    Supprime un message de contact (admin uniquement).

    Args:
        message_id: ID du message à supprimer

    Returns:
        Confirmation de la suppression

    Raises:
        HTTPException: Erreur 404 si message non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await contact_service.delete_contact_message(message_id)
        await log_action(
            admin_email="admin",
            action="contact.delete",
            entity_type="contact",
            entity_id=str(message_id),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.post("/contact/{message_id}/reply", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def reply_to_contact_message(message_id: int, reply_data: ContactReplyRequest) -> Dict[str, Any]:
    """
    Répond à un message de contact par email (admin uniquement).

    L'email est envoyé au contact et le statut du message est automatiquement
    mis à jour vers 'processed'.

    Args:
        message_id: ID du message auquel répondre
        reply_data: Contenu de la réponse

    Returns:
        Confirmation de l'envoi

    Raises:
        HTTPException: Erreur 404 si message non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await contact_service.reply_to_contact(message_id, reply_data.body)
        await log_action(
            admin_email="admin",
            action="contact.reply",
            entity_type="contact",
            entity_id=str(message_id),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")
