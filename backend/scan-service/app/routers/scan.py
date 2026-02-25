"""Route de scan (posture sécurité) — validation d'URL + protection SSRF."""

from fastapi import APIRouter, HTTPException

from app.config_loader import get_ssrf_settings
from app.schemas.scan import ScanRequest, ScanValidationResponse
from app.utils.ssrf import check_ssrf
from app.utils.url_validator import URLValidationError, validate_and_normalize_url

router = APIRouter(prefix="/api", tags=["scan"])


@router.post(
    "/scan",
    response_model=ScanValidationResponse,
    summary="Lancer un scan",
    description="Valide l'URL (schéma, ports, SSRF) et retourne l'URL normalisée.",
)
async def post_scan(body: ScanRequest) -> ScanValidationResponse:
    """Valide l'URL fournie et retourne l'URL normalisée.

    Vérifications : schéma http/https, pas de credentials, ports 80/443,
    longueur limitée, protection SSRF (localhost et IP privées bloquées).

    Args:
        body: Corps de la requête contenant l'URL à scanner.

    Returns:
        ScanValidationResponse: URL validée et normalisée.

    Raises:
        HTTPException: 400 si l'URL est invalide ou cible une IP/host interdit.
    """
    try:
        normalized_url = validate_and_normalize_url(body.url)
        await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ScanValidationResponse(valid=True, url=normalized_url)
