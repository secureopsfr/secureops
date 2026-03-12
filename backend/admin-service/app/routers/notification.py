"""Router pour les routes admin des emails de notification."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.schemas.common import (
    ErrorResponse,
    NotificationEmailCreateResponse,
    NotificationEmailRequest,
    NotificationEmailScheduleRequest,
    NotificationSendRequest,
)
from app.services.notification_service import NotificationService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_50 = Query(50)
DEFAULT_QUERY_0 = Query(0)

router = APIRouter()

# Instance du service
notification_service = NotificationService()


def _delete_notification_email_sync(email_id: int) -> Dict[str, Any]:
    """Supprime un email de notification via session sync (hors boucle async)."""
    from app.db_sync import get_sync_session
    from app.models.email import NotificationEmail

    with get_sync_session() as db:
        email = db.query(NotificationEmail).filter(NotificationEmail.id == email_id).first()
        if not email:
            raise ValueError(f"Email {email_id} non trouvé")
        db.delete(email)
        db.commit()
        return {"message": f"Email {email_id} supprimé avec succès", "email_id": email_id}


def _get_scheduled_notifications_sync() -> Dict[str, Any]:
    """Récupère les notifications programmées via session sync."""
    from datetime import datetime, timezone

    from app.db_sync import get_sync_session
    from app.models.email import NotificationEmail

    with get_sync_session() as db:
        scheduled_emails = (
            db.query(NotificationEmail)
            .filter(NotificationEmail.status == "scheduled", NotificationEmail.scheduled_at > datetime.now(timezone.utc))
            .all()
        )
        emails_list = [
            {
                "id": email.id,
                "subject": email.subject,
                "scheduled_at": email.scheduled_at.isoformat() if email.scheduled_at else None,
            }
            for email in scheduled_emails
        ]
        return {"scheduled_emails": emails_list, "count": len(emails_list)}


def _cancel_scheduled_notification_sync(email_id: int) -> Dict[str, Any]:
    """Annule une notification planifiée via session sync."""
    from app.db_sync import get_sync_session
    from app.models.email import NotificationEmail

    with get_sync_session() as db:
        email = db.query(NotificationEmail).filter(NotificationEmail.id == email_id, NotificationEmail.status == "scheduled").first()
        if not email:
            raise ValueError(f"Email {email_id} non trouvé ou non programmé")

        email.status = "draft"
        email.is_scheduled = False
        email.scheduled_at = None
        db.commit()
        return {"message": f"Programmation de l'email {email_id} annulée avec succès", "email_id": email_id, "status": "draft"}


@router.get("/notifications", responses={500: {"model": ErrorResponse}})
async def get_notification_emails(limit: int = DEFAULT_QUERY_50, offset: int = DEFAULT_QUERY_0) -> Dict[str, Any]:
    """
    Récupère la liste des emails de notification avec pagination (admin uniquement).

    Args:
        limit: Nombre maximum d'emails
        offset: Nombre d'emails à ignorer

    Returns:
        dict: {data: [...], total, page, per_page, total_pages}

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        result = await notification_service.get_notification_emails(limit=limit, offset=offset)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post(
    "/notifications",
    response_model=NotificationEmailCreateResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_notification_email(email_data: NotificationEmailRequest) -> NotificationEmailCreateResponse:
    """
    Crée un nouvel email de notification (admin uniquement).

    Args:
        email_data: Données de l'email de notification à créer

    Returns:
        NotificationEmailCreateResponse: Confirmation de création de l'email

    Raises:
        HTTPException: Erreur 400 si données invalides, 500 en cas d'erreur serveur
    """
    try:
        result = await notification_service.create_notification_email(email_data)
        return NotificationEmailCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.put(
    "/notifications/{email_id}",
    response_model=NotificationEmailCreateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def update_notification_email(email_id: int, email_data: NotificationEmailRequest) -> NotificationEmailCreateResponse:
    """
    Met à jour un email de notification (admin uniquement).

    Args:
        email_id: ID de l'email à mettre à jour
        email_data: Nouvelles données de l'email de notification

    Returns:
        NotificationEmailCreateResponse: Confirmation de mise à jour de l'email

    Raises:
        HTTPException: Erreur 400 si données invalides, 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await notification_service.update_notification_email(email_id, email_data)
        return NotificationEmailCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")


@router.delete("/notifications/{email_id}", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def delete_notification_email(email_id: int) -> Dict[str, Any]:
    """
    Supprime un email de notification (admin uniquement).

    Args:
        email_id: ID de l'email à supprimer

    Returns:
        dict: Confirmation de suppression

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_delete_notification_email_sync, email_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post("/notifications/send", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def send_notification_email(send_data: NotificationSendRequest) -> Dict[str, Any]:
    """
    Envoie un email de notification à tous les abonnés vérifiés (admin uniquement).

    Args:
        send_data: Données contenant l'ID de l'email à envoyer

    Returns:
        dict: Confirmation d'envoi

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await notification_service.send_notification_email(send_data.email_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post(
    "/notifications/schedule",
    response_model=dict,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def schedule_notification_email(schedule_data: NotificationEmailScheduleRequest) -> Dict[str, Any]:
    """
    Programme l'envoi d'un email de notification (admin uniquement).

    Args:
        schedule_data: Données contenant l'ID de l'email et la date de programmation

    Returns:
        dict: Confirmation de programmation

    Raises:
        HTTPException: Erreur 400 si données invalides, 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(notification_service.schedule_notification_email, schedule_data.email_id, schedule_data.scheduled_at)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.get("/notifications/scheduled", response_model=dict, responses={500: {"model": ErrorResponse}})
async def get_scheduled_notifications() -> Dict[str, Any]:
    """
    Récupère la liste des emails de notification programmés (admin uniquement).

    Returns:
        dict: Liste des emails programmés

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_get_scheduled_notifications_sync)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post(
    "/notifications/cancel-schedule/{email_id}", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def cancel_scheduled_notification(email_id: int) -> Dict[str, Any]:
    """
    Annule la programmation d'un email de notification (admin uniquement).

    Args:
        email_id: ID de l'email à annuler

    Returns:
        dict: Confirmation d'annulation

    Raises:
        HTTPException: Erreur 404 si email non trouvé ou non programmé, 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_cancel_scheduled_notification_sync, email_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
