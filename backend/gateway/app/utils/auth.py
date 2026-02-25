"""
Module d'authentification pour l'API Gateway.

Ce module fournit des dépendances FastAPI pour l'authentification
et l'extraction des informations utilisateur depuis les tokens JWT.
"""

import logging
from typing import Any, Dict, Optional

from common.jwt_verifier import verify_cognito_jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

# Schéma de sécurité HTTP Bearer pour FastAPI
security = HTTPBearer()


def get_current_user(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> Dict[str, Any]:  # noqa: B008
    """
    Extrait et vérifie l'utilisateur depuis le token JWT dans le header Authorization.

    Cette fonction :
    1. Vérifie que le header Authorization commence par "Bearer "
    2. Extrait le token JWT
    3. Vérifie le token avec verify_cognito_jwt
    4. Retourne les claims (informations utilisateur)

    Args:
        authorization (Optional[str]): Le header Authorization contenant le token Bearer.

    Returns:
        Dict[str, Any]: Les claims du token JWT (informations utilisateur).

    Raises:
        HTTPException: Si le token est manquant, invalide ou expiré.
    """
    if not authorization:
        logger.warning("Header Authorization manquant")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Vérifier que Authorization commence par "Bearer "
    if not authorization.startswith("Bearer "):
        logger.warning("Format Authorization invalide: %s...", authorization[:20])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format Authorization invalide. Attendu: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extraire le token (enlever "Bearer " du début)
    token = authorization[7:].strip()

    if not token:
        logger.warning("Token JWT manquant après 'Bearer '")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Vérifier le token et obtenir les claims
        claims = verify_cognito_jwt(token)
        logger.debug("Utilisateur authentifié: %s", claims.get("sub"))  # noqa: Q000
        return claims

    except ValueError as e:
        error_msg = str(e)
        # Si le problème est lié à une clé manquante, suggérer de se reconnecter
        if "Aucune clé publique trouvée" in error_msg:
            logger.warning("Token JWT invalide (clé manquante): %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token JWT invalide ou expiré. Veuillez vous reconnecter.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.warning("Token JWT invalide: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token JWT invalide: {error_msg}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Gérer ExpiredSignatureError, JWTClaimsError, etc.
        logger.warning("Erreur de vérification JWT: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erreur d'authentification: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),  # noqa: B008
) -> Optional[Dict[str, Any]]:
    """
    Version optionnelle de get_current_user qui retourne None si l'utilisateur n'est pas authentifié.

    Utile pour les endpoints qui fonctionnent avec ou sans authentification.

    Args:
        authorization (Optional[str]): Le header Authorization contenant le token Bearer.

    Returns:
        Optional[Dict[str, Any]]: Les claims du token JWT ou None si non authentifié.
    """
    if not authorization:
        return None

    try:
        return get_current_user(authorization)
    except HTTPException:
        return None


def require_admin(user: Dict[str, Any] = Depends(dependency=get_current_user)) -> Dict[str, Any]:  # noqa: B008
    """
    Vérifie que l'utilisateur est dans le groupe "admin".

    À utiliser comme dépendance pour les routes admin.

    Args:
        user (Dict[str, Any]): Les claims du token JWT obtenus via get_current_user.

    Returns:
        Dict[str, Any]: Les claims du token JWT si l'utilisateur est admin.

    Raises:
        HTTPException: 403 Forbidden si l'utilisateur n'est pas dans le groupe "admin".
    """
    groups = user.get("cognito:groups", [])

    if "admin" not in groups:
        logger.warning("Accès admin refusé pour l'utilisateur: %s", user.get("sub"))  # noqa: Q000
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls les administrateurs peuvent accéder à cette ressource.",
        )

    return user


def require_beta_or_admin(user: Dict[str, Any] = Depends(dependency=get_current_user)) -> Dict[str, Any]:  # noqa: B008
    """
    Vérifie que l'utilisateur est dans le groupe "beta" ou "admin".

    À utiliser comme dépendance pour les routes nécessitant un accès beta tester.

    Args:
        user (Dict[str, Any]): Les claims du token JWT obtenus via get_current_user.

    Returns:
        Dict[str, Any]: Les claims du token JWT si l'utilisateur est beta ou admin.

    Raises:
        HTTPException: 403 Forbidden si l'utilisateur n'est ni dans "beta" ni dans "admin".
    """
    groups = user.get("cognito:groups", [])

    if "beta" not in groups and "admin" not in groups:
        logger.warning("Accès beta refusé pour l'utilisateur: %s", user.get("sub"))  # noqa: Q000
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls les utilisateurs beta ou les administrateurs peuvent accéder à cette ressource.",
        )

    return user
