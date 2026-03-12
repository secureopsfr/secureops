"""Router pour les routes admin de la mailing list."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.schemas.common import ErrorResponse, MailingListResponse, MailingListSubscribeResponse
from app.services.mailing_list_service import MailingListService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_QUERY_100 = Query(100)
DEFAULT_QUERY_0 = Query(0)
DEFAULT_QUERY_REQUIRED = Query(...)

router = APIRouter()

# Instance du service
mailing_list_service = MailingListService()


@router.get("/mailing-list", response_model=MailingListResponse, responses={500: {"model": ErrorResponse}})
async def get_mailing_list(limit: int = DEFAULT_QUERY_100, offset: int = DEFAULT_QUERY_0) -> MailingListResponse:
    """
    Récupère la liste de diffusion (admin uniquement).

    Args:
        limit: Nombre d'entrées par page (1-1000)
        offset: Décalage pour la pagination

    Returns:
        MailingListResponse: Liste de diffusion paginée

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(mailing_list_service.get_mailing_list, limit, offset)
        return MailingListResponse(**result)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.put(
    "/mailing-list/verify",
    response_model=MailingListSubscribeResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def verify_email(email: str = DEFAULT_QUERY_REQUIRED) -> MailingListSubscribeResponse:
    """
    Marque une adresse email comme vérifiée (admin uniquement).

    Args:
        email: Adresse email à vérifier

    Returns:
        MailingListSubscribeResponse: Confirmation de vérification

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(mailing_list_service.verify_email, email)
        return MailingListSubscribeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.delete(
    "/mailing-list/unsubscribe",
    response_model=MailingListSubscribeResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def unsubscribe_email_from_mailing_list(email: str = DEFAULT_QUERY_REQUIRED) -> MailingListSubscribeResponse:
    """
    Désinscrit une adresse email de la mailing list (admin uniquement).

    Args:
        email: Adresse email à désinscrire

    Returns:
        MailingListSubscribeResponse: Confirmation de désinscription

    Raises:
        HTTPException: Erreur 404 si email non trouvé, 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(mailing_list_service.unsubscribe_email, email)
        return MailingListSubscribeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


def _delete_subscriber_sync(email: str) -> Dict[str, Any]:
    """Supprime un abonné via session sync (exécuté hors boucle async)."""
    from app.db_sync import get_sync_session
    from app.models.user import Subscription, User

    with get_sync_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError(f"Utilisateur avec l'email {email} non trouvé")

        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if subscription:
            subscription.newsletter_enabled = False
            db.commit()
        else:
            subscription = Subscription(user_id=user.id, newsletter_enabled=False)
            db.add(subscription)
            db.commit()
        return {"message": f"Abonné {email} supprimé avec succès", "email": email}


@router.delete("/mailing-list/{email}", response_model=dict, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def delete_subscriber(email: str) -> Dict[str, Any]:
    """
    Supprime un abonné de la liste de diffusion (admin uniquement).

    Args:
        email: Adresse email de l'abonné à supprimer

    Returns:
        dict: Confirmation de suppression

    Raises:
        HTTPException: Erreur 404 si abonné non trouvé, 500 en cas d'erreur serveur
    """
    try:
        return await run_in_threadpool(_delete_subscriber_sync, email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.get("/notifications/subscribers", response_model=MailingListResponse, responses={500: {"model": ErrorResponse}})
async def get_notification_subscribers(limit: int = DEFAULT_QUERY_100, offset: int = DEFAULT_QUERY_0) -> MailingListResponse:
    """
    Récupère la liste des abonnés aux notifications (admin uniquement).

    Args:
        limit: Nombre d'entrées par page (1-1000)
        offset: Décalage pour la pagination

    Returns:
        MailingListResponse: Liste des abonnés paginée

    Raises:
        HTTPException: Erreur 500 en cas d'erreur serveur
    """
    try:
        result = await run_in_threadpool(mailing_list_service.get_notification_subscribers, limit, offset)
        return MailingListResponse(**result)
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
