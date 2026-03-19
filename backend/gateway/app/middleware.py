"""Module de middleware pour l'API Gateway."""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .config_loader import settings
from .utils.api_key_auth import _get_client_ip, authenticate_via_api_key, extract_api_key_from_request
from .utils.auth import get_current_user
from .utils.quota_client import DAILY_QUOTA_LIMIT, check_and_increment_quota
from .utils.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

# ── Routes publiques (aucune authentification) ──────────────────────
PUBLIC_EXACT: set[str] = {"/health", "/admin/api/docs"}
PUBLIC_PREFIX: tuple[str, ...] = (
    "/images/",
    "/admin/images/",
    "/admin/api/docs/",
    "/scan/api/scan/async",
    "/crawl/api/crawl/async",
)
PUBLIC_METHOD_PATHS: set[tuple[str, str]] = {
    ("POST", "/api/contact"),  # Protégé par captcha Turnstile
    ("POST", "/admin/api/analytics/ingest"),  # Protégé par validation + rate limiting
}

# ── Routes authentifiées sans vérification de groupe ────────────────
AUTH_ONLY_METHOD_PATHS: set[tuple[str, str]] = {
    ("POST", "/user/api/user/init"),  # Tout utilisateur authentifié peut init son compte
}
OPTIONAL_AUTH_PUBLIC_PREFIX: tuple[str, ...] = (
    "/scan/api/scan/async",
    "/crawl/api/crawl/async",
)

# ── Endpoints soumis au rate limiting et au quota ───────────────────
_QUOTA_PATHS: frozenset[str] = frozenset(
    {
        "/scan/api/scan/async",
        "/crawl/api/crawl/async",
    }
)


def _is_public_route(path: str, method: str) -> bool:
    """Retourne True si la route est publique (sans auth)."""
    return path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIX) or (method, path) in PUBLIC_METHOD_PATHS


def _requires_optional_public_auth(path: str) -> bool:
    """Retourne True si la route publique accepte une auth facultative."""
    return path.startswith(OPTIONAL_AUTH_PUBLIC_PREFIX)


def _has_auth_hint(request: Request) -> bool:
    """Retourne True si des headers d'auth sont présents."""
    return bool(request.headers.get("Authorization") or request.headers.get("X-API-Key"))


def _next_midnight_utc_iso() -> str:
    d = datetime.now(UTC).date()
    return (datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)).isoformat()


def _seconds_until_midnight_utc() -> int:
    d = datetime.now(UTC).date()
    midnight = datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)
    return max(1, int((midnight - datetime.now(UTC)).total_seconds()))


async def _authenticate(request: Request, *, require_admin: bool = False) -> Tuple[Optional[dict], Optional[JSONResponse]]:
    """Authentifie l'utilisateur (JWT ou clé API).

    Priorité : JWT si Bearer ressemble à un JWT, sinon clé API (X-API-Key ou Bearer).
    """
    authorization = request.headers.get("Authorization")
    x_api_key = request.headers.get("X-API-Key")

    # 1) Tenter l'auth par clé API (X-API-Key ou Bearer avec token non-JWT)
    api_key = extract_api_key_from_request(authorization, x_api_key)
    if api_key:
        client_ip = _get_client_ip(request)
        user = await authenticate_via_api_key(api_key, client_ip=client_ip)
        if user and "_error" not in user:
            if require_admin:
                # Les clés API n'ont pas de groupe admin
                return None, JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Accès refusé. Les clés API ne permettent pas l'accès admin."},
                )
            request.state.user = user
            request.state.api_key_to_forward = api_key  # Pour le proxy (historique scans)
            logger.debug("Auth via clé API: user_id=%s", user.get("user_id"))
            return user, None
        # Clé API invalide — ne pas retenter en JWT
        detail = user.get("_error", "Clé API invalide ou révoquée") if (isinstance(user, dict) and user) else "Clé API invalide ou révoquée"
        return None, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2) Auth JWT (Authorization: Bearer obligatoire)
    if not authorization:
        return None, JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentification requise"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = get_current_user(authorization)
        user["auth_type"] = "jwt"

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


def _build_rate_limit_key(request: Request, path: str, method: str) -> tuple[str, str]:
    """Construit la clé de rate limiting et retourne (key, bucket_type).

    bucket_type: "user" | "api_key" | "anon"
    """
    user = getattr(request.state, "user", None)
    if user:
        auth_type = user.get("auth_type", "jwt")
        identity = user.get("user_id") or user.get("sub") or "unknown"
        bucket = "api_key" if auth_type == "api_key" else "user"
        return f"{bucket}:{identity}:{method}:{path}", bucket
    # Anonyme : limiter par IP
    ip = _get_client_ip(request) or "unknown"
    return f"anon:{ip}:{method}:{path}", "anon"


def _check_short_term_rate_limit(request: Request, path: str, method: str) -> Optional[JSONResponse]:
    """Vérifie le rate limiting court terme (fenêtre 60 s).

    Retourne une JSONResponse 429 si dépassé, None sinon.
    """
    key, bucket = _build_rate_limit_key(request, path, method)
    limit, window = _rate_limits_for(bucket)
    allowed, retry_after = get_rate_limiter().is_allowed(key, limit=limit, window_seconds=window)
    if allowed:
        return None
    logger.warning("Rate limit court terme dépassé: bucket=%s key=%s", bucket, key)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Trop de requêtes. Veuillez patienter avant de réessayer.",
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


def _rate_limits_for(bucket: str) -> tuple[int, int]:
    """Retourne (limit, window_seconds) pour un type de bucket."""
    rl = settings().rate_limits
    bucket_conf = getattr(rl, bucket, None) or rl.user
    return bucket_conf.limit, bucket_conf.window_seconds


async def _check_long_term_quota(request: Request) -> Optional[JSONResponse]:
    """Vérifie le quota journalier (long terme) pour l'utilisateur authentifié.

    Retourne une JSONResponse 429 si le quota est épuisé, None sinon.
    Ignoré pour les utilisateurs anonymes.
    """
    user = getattr(request.state, "user", None)
    if not user:
        # Anonyme : pas de quota long terme
        return None

    cognito_sub = user.get("sub")
    if not cognito_sub:
        logger.warning("Quota check impossible : sub manquant dans request.state.user")
        return None

    allowed, remaining, reset_at = await check_and_increment_quota(
        cognito_sub,
        limit=DAILY_QUOTA_LIMIT,
    )

    if allowed:
        return None

    retry_after = _seconds_until_midnight_utc()
    logger.info("Quota journalier dépassé: sub=%s remaining=0 reset_at=%s", cognito_sub, reset_at)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Quota journalier atteint. Réessayez demain.",
            "remaining": 0,
            "limit": DAILY_QUOTA_LIMIT,
            "reset_at": reset_at or _next_midnight_utc_iso(),
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


async def _handle_public_route(request: Request, path: str, method: str, call_next) -> Response:
    """Gère les routes publiques : auth facultative, rate limit et quota si applicable."""
    if _requires_optional_public_auth(path) and _has_auth_hint(request):
        _, error_response = await _authenticate(request, require_admin=False)
        if error_response:
            return error_response

    if method == "POST" and path in _QUOTA_PATHS:
        if rl_error := _check_short_term_rate_limit(request, path, method):
            return rl_error
        if quota_error := await _check_long_term_quota(request):
            return quota_error

    return await call_next(request)


async def _handle_protected_route(request: Request, require_admin: bool, call_next) -> Response:
    """Authentifie et autorise l'accès aux routes protégées."""
    _, error_response = await _authenticate(request, require_admin=require_admin)
    return error_response or await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware d'authentification et de protection anti-abus pour la gateway.

    - Routes publiques (PUBLIC_*) : aucune authentification
    - Routes /admin/* : nécessitent le groupe « admin »
    - Autres routes : nécessitent uniquement l'authentification
    - Endpoints scan/crawl async : rate limiting court terme + quota journalier
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Middleware d'authentification pour protéger toutes les routes."""
        if os.getenv("DISABLE_AUTH_MIDDLEWARE", "false").lower() == "true":
            return await call_next(request)

        path = request.url.path
        method = request.method

        if method == "OPTIONS":
            return await call_next(request)

        if _is_public_route(path, method):
            return await _handle_public_route(request, path, method, call_next)

        require_admin = path.startswith("/admin/")
        return await _handle_protected_route(request, require_admin, call_next)
