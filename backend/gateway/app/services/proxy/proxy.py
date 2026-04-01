"""Fonctions de base de proxy pour l'API Gateway.

Contient les fonctions de proxy buffer et stream pour les requêtes vers les services backend.
"""

import logging

import httpx
from common.jwt_verifier import verify_cognito_jwt
from common.logging_config import correlation_id_ctx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTasks

from ...config_loader import settings

logger = logging.getLogger(__name__)

config = settings()
HOP_BY_HOP = set(config.headers.hop_by_hop)


def _token_looks_like_jwt(token: str) -> bool:
    return token.count(".") == 2 and all(len(p) > 0 for p in token.split(".", 2))


def _cognito_sub_from_request_authorization(request: Request) -> str | None:
    """Extrait le cognito sub depuis Authorization Bearer si JWT valide.

    Utilisé quand le middleware n'a pas rempli request.state.user (ex. DISABLE_AUTH_MIDDLEWARE=true)
    mais que le client envoie quand même un JWT : scan-service / crawl attendent X-Authenticated-User-Id.
    """
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token or not _token_looks_like_jwt(token):
        return None
    try:
        claims = verify_cognito_jwt(token)
        sub = claims.get("sub")
        return str(sub) if sub else None
    except Exception:
        logger.debug("JWT présent mais non vérifiable pour X-Authenticated-User-Id", exc_info=True)
        return None


def _log_proxy_request(service_url: str, path: str, request: Request, mode: str = "buffer") -> None:
    """Log une requête proxy (buffer ou stream) avec infos utilisateur si présentes."""
    if hasattr(request.state, "user") and request.state.user:
        u = request.state.user
        ident = u.get("username") or u.get("email") or u.get("user_id") or "unknown"
        auth_type = u.get("auth_type", "jwt")
        logger.info("Requête proxy %s de %s [%s] vers %s/%s", mode, ident, auth_type, service_url, path)
    else:
        logger.info("Requête proxy %s (sans auth) vers %s/%s", mode, service_url, path)


def _build_proxied_headers(request: Request, extra_headers: dict[str, str] | None) -> dict[str, str]:
    """Construit les headers à envoyer au backend (filtrés + extra + api_key + correlation_id)."""
    headers = {name: value for name, value in request.headers.items() if name.lower() not in HOP_BY_HOP and name.lower() != "accept-encoding"}
    if extra_headers:
        headers.update(extra_headers)
    if hasattr(request.state, "api_key_to_forward") and request.state.api_key_to_forward:
        headers["Authorization"] = f"Bearer {request.state.api_key_to_forward}"
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        # scan-service / user-service (assert DNS, jobs async) attendent le cognito_sub, pas l'UUID interne.
        # Clé API : verify renvoie user_id (UUID) et sub ; il faut privilégier sub.
        user_id = user.get("sub") or user.get("user_id")
        if user_id:
            headers["X-Authenticated-User-Id"] = str(user_id)
    elif "x-authenticated-user-id" not in {k.lower() for k in headers}:
        derived_sub = _cognito_sub_from_request_authorization(request)
        if derived_sub:
            headers["X-Authenticated-User-Id"] = derived_sub
    cid = correlation_id_ctx.get()
    if cid:
        headers["X-Correlation-ID"] = cid
    return headers


def _get_timeout_buffer(path: str) -> float:
    """Retourne le timeout pour une requête buffer."""
    if path == "api/crawl" or path.startswith("api/crawl/"):
        logger.info("Crawl endpoint : timeout étendu à %.0fs", config.timeouts.crawl_timeout)
        return config.timeouts.crawl_timeout
    return config.timeouts.request_timeout


def _get_timeout_stream(path: str) -> float:
    """Retourne le timeout pour une requête stream."""
    if path == "api/crawl/stream" or path.startswith("api/crawl/"):
        logger.info("Crawl stream : timeout étendu à %.0fs", config.timeouts.crawl_timeout)
        return config.timeouts.crawl_timeout
    return config.timeouts.request_timeout


def _filter_response_headers(resp: httpx.Response) -> dict[str, str]:
    """Filtre les headers de réponse (hop-by-hop, content-encoding, transfer-encoding)."""
    exclude = HOP_BY_HOP | {"content-encoding", "transfer-encoding"}
    return {k: v for k, v in resp.headers.items() if k.lower() not in exclude}


async def proxy_buffer_request(
    service_url: str,
    request: Request,
    path: str,
    *,
    extra_headers: dict[str, str] | None = None,
) -> tuple[Response, int | None]:
    """
    Proxy « buffer » : lit tout le contenu (JSON, CSV...) et renvoie un Response classique.

    Args:
        service_url: URL du service à proxyer.
        request: Requête HTTP.
        path: Chemin de la requête.
        extra_headers: Headers additionnels à envoyer au backend (ex. clé API interne).

    Returns:
        tuple[Response, int | None]: Réponse HTTP et taille du corps.
    """
    _log_proxy_request(service_url, path, request, "buffer")
    proxied_headers = _build_proxied_headers(request, extra_headers)

    body_content = getattr(request.state, "body", None)
    if body_content is None:
        body_content = await request.body()

    timeout = _get_timeout_buffer(path)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.request(
                request.method,
                f"{service_url}/{path}",
                headers=proxied_headers,
                content=body_content,
                params=list(request.query_params.multi_items()),
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail=f"{service_url} timeout: {exc}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"{service_url} unreachable: {exc}")

    filtered_headers = _filter_response_headers(resp)

    # 4) Calculer la taille de la réponse
    response_size_bytes = len(resp.content) if resp.content else None

    # 5) Retourner le contenu et la taille
    return (
        Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=filtered_headers,
            media_type=resp.headers.get("Content-Type"),
        ),
        response_size_bytes,
    )


async def proxy_stream_request(
    service_url: str,
    request: Request,
    path: str,
    *,
    extra_headers: dict[str, str] | None = None,
) -> StreamingResponse:
    """
    Instancie un AsyncClient(timeout=…) et fait client.send(..., stream=True).

    Args:
        service_url: URL du service à proxyer.
        request: Requête HTTP.
        path: Chemin de la requête.
        extra_headers: Headers additionnels à envoyer au backend.

    Returns:
        StreamingResponse: Réponse streaming.
    """
    _log_proxy_request(service_url, path, request, "stream")
    proxied_headers = _build_proxied_headers(request, extra_headers)
    timeout = _get_timeout_stream(path)

    # Créer le client avec timeout
    client = httpx.AsyncClient(timeout=timeout)
    # ID du background task pour fermer client+resp
    tasks = BackgroundTasks()

    try:
        # Utiliser le body depuis request.state si disponible (déjà lu pour calculer la taille)
        body_content = getattr(request.state, "body", None)
        if body_content is None:
            body_content = await request.body()

        # Construire & envoyer la requête en stream
        req = client.build_request(
            request.method,
            f"{service_url}/{path}",
            headers=proxied_headers,
            content=body_content,
            params=list(request.query_params.multi_items()),
        )
        resp = await client.send(req, stream=True)
    except httpx.TimeoutException as exc:
        await client.aclose()
        raise HTTPException(status_code=504, detail=f"{service_url} timeout: {exc}")
    except httpx.RequestError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"{service_url} unreachable: {exc}")

    filtered_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP}

    # Fermer resp+client en arrière-plan
    tasks.add_task(resp.aclose)
    tasks.add_task(client.aclose)

    # Renvoyer le flux brut + injecter CORS
    streaming = StreamingResponse(
        resp.aiter_raw(),
        status_code=resp.status_code,
        headers=filtered_headers,
        media_type=resp.headers.get("Content-Type"),
        background=tasks,
    )
    return streaming
