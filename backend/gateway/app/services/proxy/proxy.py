"""Fonctions de base de proxy pour l'API Gateway.

Contient les fonctions de proxy buffer et stream pour les requêtes vers les services backend.
"""

import logging

import httpx
from common.logging_config import correlation_id_ctx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTasks

from ...config_loader import settings

logger = logging.getLogger(__name__)

config = settings()
HOP_BY_HOP = set(config.headers.hop_by_hop)


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
    # Log des informations utilisateur si disponibles
    if hasattr(request.state, "user") and request.state.user:
        logger.info("Requête proxy buffer de %s vers %s/%s", request.state.user.get("username", "unknown"), service_url, path)  # noqa: Q000
    else:
        logger.info("Requête proxy buffer (sans auth) vers %s/%s", service_url, path)

    # 1) Filtrer les headers à forwarder
    proxied_headers = {name: value for name, value in request.headers.items() if name.lower() not in HOP_BY_HOP and name.lower() != "accept-encoding"}
    if extra_headers:
        proxied_headers.update(extra_headers)

    # Propager le correlation_id vers les services en aval
    cid = correlation_id_ctx.get()
    if cid:
        proxied_headers["X-Correlation-ID"] = cid

    # 2) Requête et bufferisation
    # Utiliser le body depuis request.state si disponible (déjà lu pour calculer la taille)
    body_content = getattr(request.state, "body", None)
    if body_content is None:
        body_content = await request.body()

    # Timeout : on désactive pour les rafraîchissements longs ; crawl SPA utilise un timeout étendu
    timeout = config.timeouts.request_timeout
    if (
        "analytics-ingestion" in service_url
        or request.url.path.startswith("/analytics-ingestion")
        or path.startswith("cadastre/refresh")
        or "land-register" in service_url
    ):
        timeout = None
    elif path == "api/crawl" or path.startswith("api/crawl/"):
        # Crawl : timeout étendu (sitemap + BFS peuvent prendre 60s+)
        timeout = config.timeouts.crawl_timeout
        logger.info("Crawl endpoint : timeout étendu à %.0fs", timeout)

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

    # 3) Filtrer les headers de réponse
    filtered_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-encoding", "transfer-encoding")
    }

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
    # Log des informations utilisateur si disponibles
    if hasattr(request.state, "user") and request.state.user:
        logger.info("Requête proxy stream de %s vers %s/%s", request.state.user.get("username", "unknown"), service_url, path)  # noqa: Q000
    else:
        logger.info("Requête proxy stream (sans auth) vers %s/%s", service_url, path)

    # Filtrer les headers à forwarder
    proxied_headers = {name: value for name, value in request.headers.items() if name.lower() not in HOP_BY_HOP and name.lower() != "accept-encoding"}
    if extra_headers:
        proxied_headers.update(extra_headers)

    # Propager le correlation_id vers les services en aval
    cid = correlation_id_ctx.get()
    if cid:
        proxied_headers["X-Correlation-ID"] = cid

    # Timeout : on désactive pour les flux longs cadastre/land-register/analytics-ingestion
    # Crawl stream : timeout étendu (sitemap + BFS peuvent prendre 60s+)
    timeout = config.timeouts.request_timeout
    if (
        "land-register" in service_url
        or "analytics-ingestion" in service_url
        or request.url.path.startswith("/analytics-ingestion")
        or path.startswith("cadastre/refresh")
    ):
        timeout = None
    elif path == "api/crawl/stream" or path.startswith("api/crawl/"):
        # Crawl stream : timeout étendu
        timeout = config.timeouts.crawl_timeout
        logger.info("Crawl stream : timeout étendu à %.0fs", timeout)

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

    # Filtrer les headers de réponse (seulement hop-by-hop)
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
    # CORS explicite pour Mapbox GL
    streaming.headers["Access-Control-Allow-Origin"] = "*"
    return streaming
