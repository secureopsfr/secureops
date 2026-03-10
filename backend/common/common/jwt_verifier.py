"""Vérification des tokens JWT Cognito — module commun.

Utilise ``PyJWT`` avec ``PyJWKClient`` pour vérifier les tokens JWT
émis par AWS Cognito.  Le client JWKS gère automatiquement le cache
et la rotation des clés.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict

import jwt
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from common.cognito import CLIENT_ID, ISSUER, JWKS_URL

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    """Crée (et met en cache) un client JWKS.

    Returns:
        PyJWKClient: client configuré pointant vers le endpoint JWKS Cognito.

    Raises:
        ValueError: si ``JWKS_URL`` n'est pas défini.
    """
    if not JWKS_URL:
        raise ValueError("COGNITO_JWKS_URL ou (COGNITO_REGION et COGNITO_USER_POOL_ID) " "doivent être définis")
    try:
        return PyJWKClient(JWKS_URL)
    except Exception as e:
        logger.error("Erreur lors de la configuration du client JWKS: %s", e)
        raise


def verify_cognito_jwt(token: str) -> Dict[str, Any]:
    """Vérifie un token JWT Cognito.

    1. Récupère la clé de signature via JWKS (avec cache automatique).
    2. Vérifie la signature RS256.
    3. Vérifie l'expiration, l'issuer et — si présente — l'audience.

    Args:
        token: le token JWT brut (sans le préfixe ``Bearer``).

    Returns:
        Dict[str, Any]: payload décodé du token.

    Raises:
        ValueError: token manquant ou mal formé.
        ExpiredSignatureError: token expiré.
        InvalidTokenError: signature ou claims invalides.
    """
    if not token:
        raise ValueError("Token JWT manquant")

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Les access tokens Cognito n'ont pas de claim « aud » ;
        # on ne vérifie l'audience que si le token en contient une
        # ET que CLIENT_ID est configuré.
        has_aud = False
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            has_aud = "aud" in unverified
        except Exception:
            pass

        verify_aud = bool(CLIENT_ID) and has_aud

        options: Dict[str, bool] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": True,
            "verify_aud": verify_aud,
        }

        decode_kwargs: Dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": ISSUER,
            "options": options,
        }
        if verify_aud and CLIENT_ID:
            decode_kwargs["audience"] = CLIENT_ID

        payload: Dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            **decode_kwargs,
        )

        logger.debug("Token JWT vérifié — sub=%s", payload.get("sub"))
        return payload

    except ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        raise
    except InvalidTokenError as e:
        logger.warning("Token JWT invalide: %s", e)
        raise
    except Exception as e:
        logger.error("Erreur inattendue lors de la vérification JWT: %s", e)
        raise ValueError(f"Erreur lors de la vérification du token: {e}") from e
