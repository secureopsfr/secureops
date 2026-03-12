"""Factories pour créer les handlers de proxy.

Contient les fonctions pour créer les handlers de proxy.
"""

import contextlib
import logging
import time

from fastapi import Request

from .metrics import schedule_metric
from .proxy import proxy_buffer_request, proxy_stream_request

logger = logging.getLogger(__name__)


async def _calculate_request_size(request: Request) -> int | None:
    """Calcule la taille de la requête en octets.

    Args:
        request (Request): Requête HTTP

    Returns:
        int | None: Taille de la requête en octets, ou None si impossible à déterminer
    """
    content_length = request.headers.get("Content-Length")
    if content_length:
        with contextlib.suppress(ValueError):
            return int(content_length)

    # Si pas de Content-Length, lire le body (attention : ne peut être lu qu'une fois)
    try:
        body = await request.body()
        request_size_bytes = len(body)
        # Remettre le body dans request.state pour que proxy_buffer_request puisse le lire
        request.state.body = body
        return request_size_bytes
    except Exception:
        return None


def make_handler(
    service_url: str,
    prefix: str,
    admin_metrics_url: str | None,
    admin_metrics_api_key: str,
    *,
    extra_headers: dict[str, str] | None = None,
):
    """
    Crée un handler pour un service donné.

    Args:
        service_url: URL du service à proxyer.
        prefix: Préfixe du service (pour les métriques).
        admin_metrics_url: URL du service admin pour les métriques.
        admin_metrics_api_key: Clé API pour les métriques.
        extra_headers: Headers additionnels à envoyer au backend (ex. clé API pdf-service).

    Returns:
        Callable: Handler pour le service donné.
    """

    async def handler(path: str, request: Request):
        """Handler pour un service donné."""
        # Calcul de la taille de la requête
        request_size_bytes = await _calculate_request_size(request)

        # Si le client demande explicitement du SSE/stream, on bascule en proxy_stream_request
        accept_header = request.headers.get("accept", "")
        wants_stream = "text/event-stream" in accept_header or "event-stream" in accept_header

        start = time.perf_counter()
        if wants_stream:
            response = await proxy_stream_request(service_url, request, path, extra_headers=extra_headers)
            response_size_bytes = None
        else:
            response, response_size_bytes = await proxy_buffer_request(service_url, request, path, extra_headers=extra_headers)
        duration_ms = (time.perf_counter() - start) * 1000

        schedule_metric(
            prefix,
            path,
            request,
            response.status_code,
            duration_ms,
            admin_metrics_url,
            admin_metrics_api_key,
            request_size_bytes,
            response_size_bytes,
        )
        return response

    return handler
