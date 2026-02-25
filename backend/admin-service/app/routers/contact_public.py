"""Router pour les routes publiques des messages de contact."""

from fastapi import APIRouter, HTTPException, Request

from app.schemas.common import ContactMessageCreateResponse, ContactMessageRequest, ErrorResponse
from app.services.contact_service import ContactService
from app.utils.turnstile import is_valid_hostname, verify_turnstile

router = APIRouter()

# Instance du service
contact_service = ContactService()


@router.post(
    "/contact",
    response_model=ContactMessageCreateResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_contact_message(contact_data: ContactMessageRequest, request: Request) -> ContactMessageCreateResponse:
    """
    Crée un nouveau message de contact.

    Args:
        contact_data: Données du message de contact incluant le token Turnstile
        request: Requête HTTP pour extraire l'IP client

    Returns:
        ContactMessageCreateResponse: Confirmation de création du message

    Raises:
        HTTPException: Erreur 400 si données invalides, 403 si captcha invalide, 500 en cas d'erreur serveur
    """
    try:
        # Extraire l'IP client
        client_ip = request.client.host if request.client else None

        # Vérifier le token Turnstile
        turnstile_result = await verify_turnstile(contact_data.turnstile_token, client_ip)

        if not turnstile_result.success:
            raise HTTPException(status_code=403, detail="Erreur de vérification captcha. Relancez la page et réessayez.")

        # Vérifier le hostname pour éviter les attaques cross-domain
        # Ne vérifier le hostname que si Turnstile est activé (hostname sera None si désactivé)
        if turnstile_result.hostname and not is_valid_hostname(turnstile_result.hostname):
            raise HTTPException(status_code=403, detail="Origine invalide pour ce captcha.")

        # Créer le message seulement si le captcha est valide
        result = await contact_service.create_contact_message(contact_data)
        return ContactMessageCreateResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")
