"""Module d'authentification pour le User Service.

Ce module fournit des dépendances FastAPI pour l'authentification
et l'extraction des informations utilisateur depuis les tokens JWT.
"""

import logging
import uuid
from typing import Annotated, Any, Dict, Optional

from common.jwt_verifier import verify_cognito_jwt
from common.logging_config import mask_email
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.exceptions import UserNotFoundError
from app.models.user import User
from app.services.api_key_repository import get_api_key_by_plain_key, update_last_used_at
from app.services.cognito_service import get_user_email
from app.services.user_repository import get_or_create_user, get_user_by_cognito_sub

logger = logging.getLogger(__name__)


async def resolve_user(session: AsyncSession, current_user: Dict[str, Any]) -> User:
    """Résout cognito_sub → User en base de données (utilise la session fournie).

    Args:
        session: Session SQLAlchemy déjà ouverte.
        current_user: Dict des claims JWT (doit contenir "sub").

    Returns:
        User: L'utilisateur en base.

    Raises:
        HTTPException: 401 si sub manquant, 404 si utilisateur non trouvé.
    """
    cognito_sub = current_user.get("sub")
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Impossible d'identifier l'utilisateur",
        )
    user = await get_user_by_cognito_sub(session, cognito_sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé en base de données",
        )
    return user


async def resolve_user_id(current_user: Dict[str, Any]) -> uuid.UUID:
    """Résout cognito_sub → user_id en base de données.

    Args:
        current_user: Dict des claims JWT (doit contenir "sub").

    Returns:
        uuid.UUID: L'identifiant utilisateur en base.

    Raises:
        HTTPException: 401 si sub manquant, 404 si utilisateur non trouvé.
    """
    async with get_async_session() as session:
        user = await resolve_user(session, current_user)
        return user.id


async def get_current_user(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
) -> Dict[str, Any]:
    """Extrait et vérifie l'utilisateur depuis le token JWT dans le header Authorization.

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
        logger.warning("Format Authorization invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format Authorization invalide. Attendu: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:].strip()

    if not token:
        logger.warning("Token JWT manquant")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Détection clé API vs JWT : JWT = 3 parties base64 séparées par des points
    is_likely_jwt = token.count(".") == 2 and all(len(p) > 0 for p in token.split(".", 2))

    if not is_likely_jwt:
        # Traiter comme clé API
        return await _get_user_from_api_key(token)

    try:
        # Vérifier le token et obtenir les claims
        logger.info("Vérification du token JWT...")
        claims = verify_cognito_jwt(token)
        claims["auth_type"] = "jwt"
        logger.info("Token vérifié, sub=%s", claims.get("sub"))

        # Lazy user creation : créer l'utilisateur en base au premier appel
        cognito_sub = claims.get("sub")
        is_new_user = False
        if cognito_sub:
            logger.info("Démarrage de la création lazy pour cognito_sub=%s", cognito_sub)
            is_new_user = await _ensure_user_in_db(cognito_sub, claims)
            logger.info("Création lazy terminée pour cognito_sub=%s, is_new=%s", cognito_sub, is_new_user)
        else:
            logger.warning("Pas de 'sub' dans les claims du token")

        # Ajouter le flag is_new_user aux claims pour le frontend
        claims["is_new_user"] = is_new_user
        return claims

    except ValueError as e:
        logger.error("Token JWT invalide: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Gérer ExpiredSignatureError, InvalidTokenError, etc.
        error_type = type(e).__name__
        logger.error("Erreur de vérification JWT (%s): %s", error_type, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> uuid.UUID:
    """Dépendance FastAPI retournant directement l'identifiant utilisateur.

    À utiliser dans les endpoints qui n'ont besoin que de user_id.
    Résout cognito_sub → user en base et retourne user.id.

    Args:
        current_user: Injecté par Depends(get_current_user).

    Returns:
        uuid.UUID: L'identifiant utilisateur en base.

    Raises:
        HTTPException: 401 si sub manquant, 404 si utilisateur non trouvé.
    """
    return await resolve_user_id(current_user)


async def require_jwt_user(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> Dict[str, Any]:
    """Exige une authentification JWT (et refuse les clés API)."""
    if current_user.get("auth_type") != "jwt":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette opération nécessite une authentification utilisateur JWT.",
        )
    return current_user


async def _get_user_from_api_key(plain_key: str) -> Dict[str, Any]:
    """Résout une clé API en dict de claims (compatible avec resolve_user)."""
    async with get_async_session() as session:
        api_key = await get_api_key_by_plain_key(session, plain_key)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API invalide ou révoquée",
                headers={"WWW-Authenticate": "Bearer"},
            )
        await update_last_used_at(session, api_key)
        await session.commit()
        user = api_key.user
        return {
            "sub": user.cognito_sub,
            "email": user.email,
            "auth_type": "api_key",
        }


async def _ensure_user_in_db(cognito_sub: str, claims: Dict[str, Any]) -> bool:
    """Assure que l'utilisateur existe en base de données (lazy creation).

    Args:
        cognito_sub (str): Identifiant Cognito (sub) de l'utilisateur.
        claims (Dict[str, Any]): Claims du token JWT.

    Returns:
        bool: True si l'utilisateur vient d'être créé, False sinon.
    """
    try:
        # Récupérer l'email depuis les claims ou depuis Cognito
        email = claims.get("email")
        username = claims.get("username")  # Peut être l'email ou le sub selon la config Cognito

        logger.info(
            "Tentative de création lazy pour cognito_sub=%s, email depuis claims=%s, username=%s",
            cognito_sub,
            mask_email(email) if email else None,
            username,
        )

        if not email:
            # Si l'email n'est pas dans le token d'accès, le récupérer depuis Cognito
            # Essayer d'abord avec le username (peut être l'email), sinon avec le sub
            logger.info("Email absent des claims, récupération depuis Cognito")
            try:
                # Essayer avec le username d'abord (souvent c'est l'email)
                if username and username != cognito_sub:
                    email = get_user_email(username)
                    logger.info("Email récupéré depuis Cognito avec username: %s", mask_email(email))

                # Si toujours pas d'email, essayer avec le sub
                if not email:
                    email = get_user_email(cognito_sub)
                    logger.info("Email récupéré depuis Cognito avec sub: %s", mask_email(email))
            except UserNotFoundError:
                logger.warning("Utilisateur non trouvé dans Cognito (username=%s, sub=%s)", username, cognito_sub)
                return False
            except Exception as e:
                logger.error("Erreur lors de la récupération de l'email depuis Cognito: %s", e, exc_info=True)
                return False

        if not email:
            logger.warning("Impossible de récupérer l'email pour l'utilisateur %s", cognito_sub)
            return False

        # Créer ou récupérer l'utilisateur en base
        logger.info("Création/récupération de l'utilisateur en base: cognito_sub=%s, email=%s", cognito_sub, mask_email(email))
        async with get_async_session() as session:
            user, is_new_user = await get_or_create_user(session, cognito_sub, email)
            logger.info(
                "Utilisateur créé/récupéré en base: id=%s, cognito_sub=%s, email=%s, is_new=%s",
                user.id,
                user.cognito_sub,
                mask_email(user.email),
                is_new_user,
            )
            return is_new_user
    except Exception as e:
        # Ne pas bloquer l'authentification si la création en base échoue
        # On log juste l'erreur pour le debugging
        logger.error("Erreur lors de la création lazy de l'utilisateur %s: %s", cognito_sub, e, exc_info=True)
        return False
