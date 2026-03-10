"""Authentification par clé API (appel au user-service)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Optional

import httpx

if TYPE_CHECKING:
    from starlette.requests import Request

from ..config_loader import get_services_config

logger = logging.getLogger(__name__)

VERIFY_TIMEOUT = 5.0


@lru_cache
def _get_user_service_url() -> str | None:
    """Retourne l'URL du user-service depuis la configuration du gateway."""
    services = get_services_config()
    user_svc = next((s for s in services if s["prefix"] == "user"), None)
    if not user_svc:
        return None
    return str(user_svc["url"])


def _is_likely_jwt(token: str) -> bool:
    """Détecte si le token ressemble à un JWT (3 parties base64)."""
    return token.count(".") == 2 and all(len(p) > 0 for p in token.split(".", 2))


def _get_client_ip(request: "Request") -> str | None:
    """Extrait l'IP du client depuis la requête (X-Forwarded-For, X-Real-IP, ou client)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.scope.get("client"):
        host, _ = request.scope["client"]
        return host
    return None


async def authenticate_via_api_key(
    api_key: str,
    *,
    client_ip: str | None = None,
) -> Optional[dict[str, Any]]:
    """Vérifie une clé API auprès du user-service et retourne les infos utilisateur.

    Args:
        api_key: Clé API en clair.
        client_ip: IP du client (pour restriction IP). Optionnel.

    Returns:
        dict avec sub, email, user_id, auth_type="api_key" si valide, None sinon.
    """
    user_service_url = _get_user_service_url()
    if not user_service_url:
        logger.warning("User service non configuré, impossible de vérifier la clé API")
        return None

    url = f"{user_service_url.rstrip('/')}/api/internal/keys/verify"
    internal_key = os.getenv("USER_SERVICE_INTERNAL_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if internal_key:
        headers["X-Internal-Api-Key"] = internal_key

    payload: dict[str, Any] = {"key": api_key.strip()}
    if client_ip:
        payload["client_ip"] = client_ip

    try:
        async with httpx.AsyncClient(timeout=VERIFY_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.debug("Vérification clé API échouée: %s %s", resp.status_code, resp.text)
                try:
                    err = resp.json()
                    detail = err.get("detail", "Clé API invalide ou révoquée")
                    if isinstance(detail, str):
                        return {"_error": detail}
                except Exception:
                    pass
                return None
            data = resp.json()
            return {
                "sub": data["sub"],
                "email": data["email"],
                "user_id": data["user_id"],
                "auth_type": "api_key",
            }
    except Exception as e:
        logger.warning("Erreur vérification clé API: %s", e)
        return None


def extract_api_key_from_request(authorization: Optional[str], x_api_key: Optional[str]) -> Optional[str]:
    """Extrait la clé API depuis les headers (X-API-Key ou Bearer si non-JWT)."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token and not _is_likely_jwt(token):
            return token
    return None
