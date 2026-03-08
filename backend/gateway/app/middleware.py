"""Module de middleware pour l'API Gateway."""

import logging
import os
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .utils.auth import get_current_user

logger = logging.getLogger(__name__)

# ── Routes publiques (aucune authentification) ──────────────────────
PUBLIC_EXACT: set[str] = {"/health"}
PUBLIC_PREFIX: tuple[str, ...] = ("/images/", "/admin/images/")
PUBLIC_METHOD_PATHS: set[tuple[str, str]] = {
    ("POST", "/api/contact"),  # Protégé par captcha Turnstile
    ("POST", "/admin/api/analytics/ingest"),  # Protégé par validation + rate limiting
    ("POST", "/scan/api/scan"),  # MVP : scan posture sécurité public (disclaimer côté front)
    ("POST", "/crawl/api/crawl/stream"),  # Crawler HTTP en streaming SSE (roadmap §7)
}

# ── Routes authentifiées sans vérification de groupe ────────────────
AUTH_ONLY_METHOD_PATHS: set[tuple[str, str]] = {
    ("POST", "/user/api/user/init"),  # Tout utilisateur authentifié peut init son compte
}


def _authenticate(request: Request, *, require_admin: bool = False) -> Tuple[Optional[dict], Optional[JSONResponse]]:
    """Authentifie l'utilisateur à partir du header Authorization.

    Returns:
        (user, None) en cas de succès, (None, error_response) en cas d'échec.
    """
    authorization = request.headers.get("Authorization")
    try:
        user = get_current_user(authorization)

        if require_admin:
            groups = user.get("cognito:groups", [])
            if "admin" not in groups:
                return None, JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Accès refusé. Seuls les administrateurs peuvent accéder à cette ressource."},
                )

        request.state.user = user
        return user, None

    except HTTPException as e:
        return None, JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers if hasattr(e, "headers") else None,
        )
    except Exception as e:
        logger.warning("Erreur d'authentification: %s", e)
        return None, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentification requise"},
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware d'authentification pour protéger toutes les routes.

    - Routes publiques (PUBLIC_*) : aucune authentification
    - Routes /admin/* : nécessitent le groupe « admin »
    - Autres routes : nécessitent uniquement l'authentification
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Middleware d'authentification pour protéger toutes les routes."""
        # Bypass complet si DISABLE_AUTH_MIDDLEWARE
        if os.getenv("DISABLE_AUTH_MIDDLEWARE", "false").lower() == "true":
            return await call_next(request)

        path = request.url.path
        method = request.method

        # Requêtes OPTIONS (preflight CORS) — toujours publiques
        if method == "OPTIONS":
            return await call_next(request)

        # Routes publiques — exact match
        if path in PUBLIC_EXACT:
            return await call_next(request)

        # Routes publiques — prefix match
        if path.startswith(PUBLIC_PREFIX):
            return await call_next(request)

        # Routes publiques — (method, path) match
        if (method, path) in PUBLIC_METHOD_PATHS:
            return await call_next(request)

        # Routes auth-only (pas de vérification de groupe)
        if (method, path) in AUTH_ONLY_METHOD_PATHS:
            _, error_response = _authenticate(request, require_admin=False)
            return error_response or await call_next(request)

        # Routes admin — nécessitent le groupe « admin »
        if path.startswith("/admin/"):
            _, error_response = _authenticate(request, require_admin=True)
            return error_response or await call_next(request)

        # Toutes les autres routes — authentification simple
        _, error_response = _authenticate(request, require_admin=False)
        return error_response or await call_next(request)
