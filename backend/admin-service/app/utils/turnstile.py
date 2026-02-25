"""Utilitaires pour la vérification des tokens Cloudflare Turnstile.

Ce module fournit des fonctions pour vérifier les tokens Turnstile
reçus du frontend contre l'API Cloudflare.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# URL de l'API Cloudflare Turnstile
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileResponse(BaseModel):
    """Réponse de l'API Cloudflare Turnstile."""

    success: bool
    challenge_ts: Optional[str] = None
    hostname: Optional[str] = None
    error_codes: Optional[list[str]] = None
    action: Optional[str] = None
    cdata: Optional[str] = None


async def verify_turnstile(token: str, ip: Optional[str] = None) -> TurnstileResponse:
    """Vérifie un token Turnstile auprès de Cloudflare.

    Args:
        token: Le token Turnstile reçu du frontend
        ip: L'adresse IP du client (optionnel mais recommandé)

    Returns:
        TurnstileResponse: La réponse de Cloudflare

    Raises:
        HTTPException: Si la vérification échoue ou si Turnstile est désactivé
    """
    # Lire directement depuis les variables d'environnement
    turnstile_enabled = os.getenv("TURNSTILE_ENABLED", "false").lower() in ("true", "1", "yes")
    turnstile_secret_key = os.getenv("TURNSTILE_SECRET_KEY", "")

    # Vérifier si Turnstile est activé
    if not turnstile_enabled:
        logger.warning("Tentative de vérification Turnstile alors que le service est désactivé")
        # En mode désactivé, on accepte toujours (pour les tests/dev)
        return TurnstileResponse(success=True)

    # Vérifier que la clé secrète est configurée
    if not turnstile_secret_key:
        logger.error("TURNSTILE_SECRET_KEY non configurée")
        # En production, on cache l'erreur pour éviter de révéler la config
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Service captcha temporairement indisponible")

    # Préparer les données pour l'API Cloudflare
    data = {
        "secret": turnstile_secret_key,
        "response": token,
    }

    # Ajouter l'IP si fournie
    if ip:
        data["remoteip"] = ip

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

            if response.status_code != 200:
                logger.error("Erreur API Cloudflare: %s", response.status_code)
                return TurnstileResponse(success=False, error_codes=["api_error"])

            result = response.json()
            turnstile_response = TurnstileResponse(**result)

            # Log détaillé pour monitoring
            logger.info(
                "Vérification Turnstile réussie",
                extra={
                    "turnstile_success": turnstile_response.success,
                    "turnstile_hostname": turnstile_response.hostname,
                    "client_ip": ip,
                },
            )

            return turnstile_response

    except Exception as e:
        logger.error("Erreur lors de la vérification Turnstile: %s", e)
        return TurnstileResponse(success=False, error_codes=["network_error"])


def is_valid_hostname(hostname: Optional[str]) -> bool:
    """Vérifie que le hostname est autorisé.

    Les hostnames autorisés sont lus depuis la variable d'environnement
    TURNSTILE_ALLOWED_HOSTNAMES (liste séparée par des virgules).
    Si la variable n'est pas définie, utilise la liste par défaut.

    Args:
        hostname: Le hostname retourné par Cloudflare

    Returns:
        bool: True si le hostname est autorisé
    """
    if not hostname:
        return False

    # Lire depuis la variable d'environnement ou utiliser la liste par défaut
    allowed_hostnames_env = os.getenv("TURNSTILE_ALLOWED_HOSTNAMES")
    if allowed_hostnames_env:
        # Parser la liste séparée par des virgules et nettoyer les espaces
        allowed_hostnames = [h.strip() for h in allowed_hostnames_env.split(",") if h.strip()]
    else:
        # Liste par défaut si la variable d'environnement n'est pas définie
        allowed_hostnames = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
        ]

    # Vérifier si le hostname correspond exactement
    if hostname in allowed_hostnames:
        logger.info("Hostname autorisé (exact match): %s", hostname)
        return True

    # Vérifier si le hostname commence par un hostname autorisé (pour gérer les ports en développement)
    # Ex: "localhost:5173" correspond à "localhost"
    for allowed in allowed_hostnames:
        if hostname.startswith(allowed + ":"):
            logger.info("Hostname autorisé (avec port): %s (base: %s)", hostname, allowed)
            return True

    # En développement, être plus permissif : accepter tout hostname contenant "localhost" ou "127.0.0.1"
    is_dev = os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev", "local")
    if is_dev and ("localhost" in hostname.lower() or "127.0.0.1" in hostname.lower()):
        logger.info("Hostname autorisé (mode dev): %s", hostname)
        return True

    logger.warning("Hostname non autorisé: %s (allowed: %s)", hostname, allowed_hostnames)
    return False
