"""Route de scan (posture sécurité) — validation d'URL uniquement pour l'instant."""

from fastapi import APIRouter, HTTPException

from app.schemas.scan import ScanRequest, ScanValidationResponse
from app.utils.url_validator import URLValidationError, validate_and_normalize_url

router = APIRouter(prefix="/api", tags=["scan"])


@router.post(
    "/scan",
    response_model=ScanValidationResponse,
    summary="Lancer un scan",
    description="Valide l'URL et prépare le scan (étape actuelle : validation uniquement).",
)
async def post_scan(body: ScanRequest) -> ScanValidationResponse:
    """Valide l'URL fournie et retourne l'URL normalisée.

    Vérifications appliquées : schéma http/https, pas de credentials dans l'URL,
    ports 80/443, longueur limitée. Le scan effectif sera ajouté ultérieurement.

    Args:
        body: Corps de la requête contenant l'URL à scanner.

    Returns:
        ScanValidationResponse: URL validée et normalisée.

    Raises:
        HTTPException: 400 si l'URL est invalide.
    """
    try:
        normalized_url = validate_and_normalize_url(body.url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ScanValidationResponse(valid=True, url=normalized_url)
