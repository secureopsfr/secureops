"""Module de fetch HTTP partagé pour le scan.

Centralise la requête HTTPS (SSL permissif, timeouts) afin d'éviter les appels
dupliqués entre TLS et Security Headers. Fournit un client partagé pour réutiliser
les connexions TCP (keep-alive) sur toute la durée du scan.
"""

import contextlib
import logging
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import AsyncIterator
from weakref import WeakKeyDictionary

import httpx

from app.config_loader import get_scan_timeouts
from app.errors.fetch_errors import FetchResult, classify_fetch_exception
from app.utils.ssl_scan import ssl_context_for_scan

logger = logging.getLogger(__name__)

# Exceptions réseau connues (connexion, timeout) — on ne log pas, comportement attendu.
_NETWORK_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)

# Compteur de requêtes HTTP par client de scan (single ou multi).
_SCAN_HTTP_REQUEST_COUNTS: WeakKeyDictionary[httpx.AsyncClient, int] = WeakKeyDictionary()
_SCAN_HTTP_REQUESTS_BY_CATEGORY: WeakKeyDictionary[httpx.AsyncClient, dict[str, int]] = WeakKeyDictionary()
_HTTP_REQUEST_CATEGORY: ContextVar[str] = ContextVar("scan_http_request_category", default="unattributed")


def _attach_request_counter(client: httpx.AsyncClient) -> None:
    """Attache un hook request pour compter chaque requête HTTP sortante."""
    _SCAN_HTTP_REQUEST_COUNTS[client] = 0
    _SCAN_HTTP_REQUESTS_BY_CATEGORY[client] = defaultdict(int)

    async def _on_request(_request: httpx.Request) -> None:
        _SCAN_HTTP_REQUEST_COUNTS[client] = _SCAN_HTTP_REQUEST_COUNTS.get(client, 0) + 1
        category = _HTTP_REQUEST_CATEGORY.get()
        category_counts = _SCAN_HTTP_REQUESTS_BY_CATEGORY.setdefault(client, defaultdict(int))
        category_counts[category] = int(category_counts.get(category, 0)) + 1

    client.event_hooks.setdefault("request", []).append(_on_request)


def get_scan_http_request_count(client: httpx.AsyncClient) -> int:
    """Retourne le nombre de requêtes HTTP émises par ce client de scan."""
    return int(_SCAN_HTTP_REQUEST_COUNTS.get(client, 0))


def get_scan_http_requests_by_category(client: httpx.AsyncClient) -> dict[str, int]:
    """Retourne le détail des requêtes HTTP par catégorie pour ce client."""
    return dict(_SCAN_HTTP_REQUESTS_BY_CATEGORY.get(client, {}))


@contextmanager
def http_request_category(category: str) -> Iterator[None]:
    """Tague les requêtes HTTP du contexte courant avec une catégorie donnée."""
    token = _HTTP_REQUEST_CATEGORY.set(category)
    try:
        yield
    finally:
        _HTTP_REQUEST_CATEGORY.reset(token)


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
    _attach_request_counter(client)
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


async def get_with_client_or_error(
    client: httpx.AsyncClient,
    url: str,
    *,
    follow_redirects: bool = True,
) -> FetchResult:
    """Effectue un GET et retourne un FetchResult avec classification d'erreur.

    Utilisé pour le fetch HTTPS principal du scan : en cas d'échec, le résultat
    contient error_type, message et status_code pour l'événement SSE error.

    Args:
        client: Client httpx (ex. issu de scan_client()).
        url: URL complète à récupérer.
        follow_redirects: Si True, suit les redirections.

    Returns:
        FetchResult: Succès (response) ou échec (error_type, message, status_code).
    """
    try:
        response = await client.get(url, follow_redirects=follow_redirects)
        return FetchResult(
            success=True,
            response=response,
            error_type="",
            message="",
            status_code=response.status_code,
            details=None,
        )
    except Exception as e:
        if isinstance(e, _NETWORK_EXCEPTIONS):
            return classify_fetch_exception(e)
        logger.warning("Erreur HTTP inattendue lors du GET %s : %s", url, e, exc_info=True)
        return classify_fetch_exception(e)


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
