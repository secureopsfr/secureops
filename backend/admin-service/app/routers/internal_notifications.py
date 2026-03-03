"""Endpoints internes pour les notifications (appels service-to-service).

Protégés par X-Internal-Api-Key si ADMIN_SERVICE_INTERNAL_API_KEY est définie.
"""

import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.email_config import send_scan_alert_email

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("ADMIN_SERVICE_INTERNAL_API_KEY")

_X_INTERNAL_API_KEY_HEADER = Header(default=None, alias="X-Internal-Api-Key")


async def _verify_internal_api_key(
    x_internal_api_key: str | None = _X_INTERNAL_API_KEY_HEADER,
) -> None:
    """Vérifie la clé API interne si ADMIN_SERVICE_INTERNAL_API_KEY est définie."""
    if not INTERNAL_API_KEY:
        return
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API interne invalide ou manquante")


_VERIFY_INTERNAL_API_KEY = Depends(_verify_internal_api_key)

router = APIRouter(prefix="/api/internal/notifications", tags=["internal"])


class ScanAlertRequest(BaseModel):
    """Requête pour une alerte de scan planifié."""

    to_email: str = Field(..., description="Email du destinataire")
    url: str = Field(..., description="URL scannée")
    subject: str = Field(..., description="Sujet de l'email")
    message: str = Field(..., description="Message descriptif")
    severity: str = Field(default="warning", description="Gravité (warning, critical)")
    alert_type: str = Field(..., description="Type: regression ou critical_finding")


@router.post(
    "/scan-alert",
    summary="[Interne] Envoyer une alerte de scan à un utilisateur",
    description="Appelé par user-service (scheduler) pour les alertes de régression ou finding critical.",
)
async def post_scan_alert(
    body: ScanAlertRequest,
    _: None = _VERIFY_INTERNAL_API_KEY,
) -> dict:
    """Envoie l'email d'alerte scan au destinataire."""
    ok = send_scan_alert_email(
        to_email=body.to_email,
        url=body.url,
        subject=body.subject,
        message=body.message,
        severity=body.severity,
        alert_type=body.alert_type,
    )
    return {"success": ok}
