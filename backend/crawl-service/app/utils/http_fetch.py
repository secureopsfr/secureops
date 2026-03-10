"""Module de fetch HTTP partagé pour le crawl.

Client httpx configuré avec timeouts adaptés au crawl.
"""

import contextlib
import logging
from typing import AsyncIterator

import httpx

from app.config_loader import get_crawler_settings
from app.utils.ssl_scan import ssl_context_for_scan

logger = logging.getLogger(__name__)

_NETWORK_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


def _create_crawl_client(*, follow_redirects: bool = True) -> httpx.AsyncClient:
    """Crée un AsyncClient configuré pour le crawl (SSL permissif, timeouts)."""
    settings = get_crawler_settings()
    timeout_val = min(settings.timeout_seconds, 120.0)
    return httpx.AsyncClient(
        verify=ssl_context_for_scan(),
        follow_redirects=follow_redirects,
        timeout=httpx.Timeout(10.0, read=timeout_val),
    )


@contextlib.asynccontextmanager
async def scan_client() -> AsyncIterator[httpx.AsyncClient]:
    """Contexte client HTTP partagé pour le crawl.

    Yields:
        httpx.AsyncClient: Client configuré (SSL permissif, timeouts).
    """
    client = _create_crawl_client(follow_redirects=True)
    async with client:
        yield client


async def get_with_client(
    client: httpx.AsyncClient,
    url: str,
    *,
    follow_redirects: bool = True,
) -> httpx.Response | None:
    """Effectue un GET avec un client existant.

    Returns:
        httpx.Response | None: La réponse ou None en cas d'erreur.
    """
    try:
        response = await client.get(url, follow_redirects=follow_redirects)
        return response
    except _NETWORK_EXCEPTIONS:
        return None
    except Exception as e:
        logger.warning("Erreur HTTP inattendue lors du GET %s : %s", url, e, exc_info=True)
        return None
