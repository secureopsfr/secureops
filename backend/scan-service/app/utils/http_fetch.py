"""Module de fetch HTTP partagé pour le scan.

Centralise la requête HTTPS (SSL permissif, timeouts) afin d'éviter les appels
dupliqués entre TLS et Security Headers. Fournit un client partagé pour réutiliser
les connexions TCP (keep-alive) sur toute la durée du scan.
"""

import contextlib
import logging
from typing import AsyncIterator

import httpx

from app.config_loader import get_scan_timeouts
from app.utils.ssl_scan import ssl_context_for_scan

logger = logging.getLogger(__name__)

# Exceptions réseau connues (connexion, timeout) — on ne log pas, comportement attendu.
_NETWORK_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


def _create_scan_client(*, follow_redirects: bool = True) -> httpx.AsyncClient:
    """Crée un AsyncClient configuré pour le scan (SSL permissif, timeouts).

    Args:
        follow_redirects: Si True, suit les redirections.

    Returns:
        httpx.AsyncClient: Client non encore entré dans un contexte (à utiliser avec async with).
    """
    timeouts = get_scan_timeouts()
    return httpx.AsyncClient(
        verify=ssl_context_for_scan(),
        follow_redirects=follow_redirects,
        timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
    )


@contextlib.asynccontextmanager
async def scan_client() -> AsyncIterator[httpx.AsyncClient]:
    """Contexte client HTTP partagé pour toute la durée d'un scan.

    Réutilise les connexions TCP (keep-alive) entre la requête principale et les
    requêtes exposed_files. Le client est fermé automatiquement à la sortie.

    Yields:
        httpx.AsyncClient: Client configuré (SSL permissif, timeouts).
    """
    client = _create_scan_client(follow_redirects=True)
    async with client:
        yield client


async def get_with_client(
    client: httpx.AsyncClient,
    url: str,
    *,
    follow_redirects: bool = True,
) -> httpx.Response | None:
    """Effectue un GET avec un client existant.

    Args:
        client: Client httpx (ex. issu de scan_client()).
        url: URL complète à récupérer.
        follow_redirects: Si True, suit les redirections.

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


async def fetch_url(full_url: str, *, follow_redirects: bool = False) -> httpx.Response | None:
    """Effectue un GET vers l'URL complète (pour chemins sensibles, etc.).

    Args:
        full_url: URL complète (ex. https://example.com/.env).
        follow_redirects: Si True, suit les redirections.

    Returns:
        httpx.Response | None: La réponse ou None en cas d'erreur.
    """
    try:
        async with _create_scan_client(follow_redirects=follow_redirects) as client:
            return await client.get(full_url)
    except _NETWORK_EXCEPTIONS:
        return None
    except Exception as e:
        logger.warning("Erreur HTTP inattendue lors du fetch %s : %s", full_url, e, exc_info=True)
        return None
