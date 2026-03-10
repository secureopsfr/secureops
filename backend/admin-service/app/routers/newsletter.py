"""Router pour les routes admin des emails newsletter."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.schemas.common import (
    ErrorResponse,
    NewsletterEmailCreateResponse,
    NewsletterEmailRequest,
    NewsletterEmailScheduleRequest,
    NewsletterSendRequest,
)
from app.services.audit_service import log_action
from app.services.newsletter_service import NewsletterService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_50 = Query(50)
DEFAULT_QUERY_0 = Query(0)

router = APIRouter()

# Instance du service
newsletter_service = NewsletterService()


def _delete_newsletter_email_sync(email_id: int) -> Dict[str, Any]:
    """Supprime un email newsletter via session sync (hors boucle async)."""
    from app.db_sync import get_sync_session
    from app.models.email import NewsletterEmail

    with get_sync_session() as db:
        email = db.query(NewsletterEmail).filter(NewsletterEmail.id == email_id).first()
        if not email:
            raise ValueError(f"Email {email_id} non trouvé")
        db.delete(email)
        db.commit()
        return {"message": f"Email {email_id} supprimé avec succès", "email_id": email_id}


def _get_scheduled_emails_sync() -> Dict[str, Any]:
    """Récupère les emails newsletter programmés via session sync."""
    from datetime import datetime, timezone

    from app.db_sync import get_sync_session
    from app.models.email import NewsletterEmail

    with get_sync_session() as db:
        scheduled_emails = (
            db.query(NewsletterEmail).filter(NewsletterEmail.status == "scheduled", NewsletterEmail.scheduled_at > datetime.now(timezone.utc)).all()
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


def _cancel_scheduled_email_sync(email_id: int) -> Dict[str, Any]:
    """Annule un email newsletter planifié via session sync."""
    from app.db_sync import get_sync_session
    from app.models.email import NewsletterEmail

    with get_sync_session() as db:
        email = db.query(NewsletterEmail).filter(NewsletterEmail.id == email_id, NewsletterEmail.status == "scheduled").first()
        if not email:
            raise ValueError(f"Email {email_id} non trouvé ou non programmé")

        email.status = "draft"
        email.is_scheduled = False
        email.scheduled_at = None
        db.commit()
        return {"message": f"Programmation de l'email {email_id} annulée avec succès", "email_id": email_id, "status": "draft"}


@router.get("/newsletter", responses={500: {"model": ErrorResponse}})
async def get_newsletter_emails(limit: int = DEFAULT_QUERY_50, offset: int = DEFAULT_QUERY_0) -> Dict[str, Any]:
    """
    Récupère la liste des emails newsletter avec pagination (admin uniquement).

    Args:
        limit: Nombre maximum d'emails à retourner
        offset: Nombre d'emails à ignorer

    Returns:
        dict: {data: [...], total, page, per_page, total_pages}

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        result = await newsletter_service.get_newsletter_emails(limit=limit, offset=offset)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post("/newsletter", response_model=NewsletterEmailCreateResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_newsletter_email(email_data: NewsletterEmailRequest) -> NewsletterEmailCreateResponse:
    """
    Crée un nouvel email newsletter (admin uniquement).

    Args:
        email_data: Données de l'email newsletter à créer

    Returns:
        NewsletterEmailCreateResponse: Confirmation de création de l'email

    Raises:
        HTTPException: Erreur 400 si données invalides, 500 en cas d'erreur serveur
    """
    try:
        result = await newsletter_service.create_newsletter_email(email_data)
        await log_action(
            admin_email="admin",
            action="newsletter.create",
            entity_type="newsletter",
            entity_id=str(result.get("id", "")),
            details={"subject": email_data.subject},
        )
        return NewsletterEmailCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.put(
    "/newsletter/{email_id}",
    response_model=NewsletterEmailCreateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def update_newsletter_email(email_id: int, email_data: NewsletterEmailRequest) -> NewsletterEmailCreateResponse:
    """
    Met à jour un email newsletter (admin uniquement).

    Args:
        email_id: ID de l'email à mettre à jour
        email_data: Nouvelles données de l'email newsletter

    Returns:
        NewsletterEmailCreateResponse: Confirmation de mise à jour de l'email

    Raises:
        HTTPException: Erreur 400 si données invalides, 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await newsletter_service.update_newsletter_email(email_id, email_data)
        return NewsletterEmailCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.delete("/newsletter/{email_id}", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def delete_newsletter_email(email_id: int) -> Dict[str, Any]:
    """
    Supprime un email newsletter (admin uniquement).

    Args:
        email_id: ID de l'email à supprimer

    Returns:
        dict: Confirmation de suppression

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_delete_newsletter_email_sync, email_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post("/newsletter/send", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def send_newsletter_email(send_data: NewsletterSendRequest) -> Dict[str, Any]:
    """
    Envoie un email newsletter à tous les abonnés vérifiés (admin uniquement).

    Args:
        send_data: Données contenant l'ID de l'email à envoyer

    Returns:
        dict: Confirmation d'envoi

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await newsletter_service.send_newsletter_email(send_data.email_id)
        await log_action(
            admin_email="admin",
            action="newsletter.send",
            entity_type="newsletter",
            entity_id=str(send_data.email_id),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post(
    "/newsletter/schedule",
    response_model=dict,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def schedule_newsletter_email(schedule_data: NewsletterEmailScheduleRequest) -> Dict[str, Any]:
    """
    Programme l'envoi d'un email newsletter (admin uniquement).

    Args:
        schedule_data: Données contenant l'ID de l'email et la date de programmation

    Returns:
        dict: Confirmation de programmation

    Raises:
        HTTPException: Erreur 400 si données invalides, 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(newsletter_service.schedule_newsletter_email, schedule_data.email_id, schedule_data.scheduled_at)
        await log_action(
            admin_email="admin",
            action="newsletter.schedule",
            entity_type="newsletter",
            entity_id=str(schedule_data.email_id),
            details={"scheduled_at": schedule_data.scheduled_at},
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.get("/newsletter/scheduled", response_model=dict, responses={500: {"model": ErrorResponse}})
async def get_scheduled_emails() -> Dict[str, Any]:
    """
    Récupère la liste des emails programmés (admin uniquement).

    Returns:
        dict: Liste des emails programmés

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_get_scheduled_emails_sync)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post("/newsletter/cancel-schedule/{email_id}", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def cancel_scheduled_email(email_id: int) -> Dict[str, Any]:
    """
    Annule la programmation d'un email newsletter (admin uniquement).

    Args:
        email_id: ID de l'email à annuler

    Returns:
        dict: Confirmation d'annulation

    Raises:
        HTTPException: Erreur 404 si email non trouvé ou non programmé, 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_cancel_scheduled_email_sync, email_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
