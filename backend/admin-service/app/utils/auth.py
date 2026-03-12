"""Dépendances d'authentification pour les routes admin du service."""

from __future__ import annotations

from typing import Any

from common.jwt_verifier import verify_cognito_jwt
from fastapi import Header, HTTPException, status


def _extract_bearer_token(authorization: str | None) -> str:
    """Extrait un token Bearer du header Authorization."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format Authorization invalide. Attendu: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def require_admin_user(
    authorization: str | None = Header(default=None, alias="Authorization"),  # noqa: B008
) -> dict[str, Any]:
    """Vérifie qu'un utilisateur JWT appartient au groupe admin."""
    token = _extract_bearer_token(authorization)
    try:
        claims = verify_cognito_jwt(token)
    except Exception as exc:  # pragma: no cover - dépend de la lib JWT
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    groups = claims.get("cognito:groups", [])
    if "admin" not in groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls les administrateurs peuvent accéder à cette ressource.",
        )
    return claims
