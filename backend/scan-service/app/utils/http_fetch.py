"""Module de fetch HTTP partagé pour le scan.

Centralise la requête HTTPS (SSL permissif, timeouts) afin d'éviter les appels
dupliqués entre TLS et Security Headers. Fournit un client partagé pour réutiliser
les connexions TCP (keep-alive) sur toute la durée du scan.
"""

import contextlib
from typing import AsyncIterator

import httpx

from app.config_loader import get_scan_timeouts
from app.utils.ssl_scan import ssl_context_for_scan
from app.utils.url_helpers import build_https_url


@contextlib.asynccontextmanager
async def scan_client() -> AsyncIterator[httpx.AsyncClient]:
    """Contexte client HTTP partagé pour toute la durée d'un scan.

    Réutilise les connexions TCP (keep-alive) entre la requête principale et les
    requêtes exposed_files. Le client est fermé automatiquement à la sortie.

    Yields:
        httpx.AsyncClient: Client configuré (SSL permissif, timeouts).
    """
    timeouts = get_scan_timeouts()
    async with httpx.AsyncClient(
        verify=ssl_context_for_scan(),
        follow_redirects=True,
        timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
    ) as client:
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
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        return None
    except Exception:
        return None


async def fetch_https(url: str, *, follow_redirects: bool = True) -> httpx.Response | None:
    """Effectue un GET HTTPS vers l'URL et retourne la réponse.

    Utilise un contexte SSL permissif (certificats non vérifiés) pour pouvoir
    scanner des sites avec certificats auto-signés ou invalides.

    Args:
        url: URL normalisée à scanner.
        follow_redirects: Si True, suit les redirections (pour récupérer la page finale).

    Returns:
        httpx.Response | None: La réponse HTTP ou None en cas d'erreur (connexion, timeout).
    """
    timeouts = get_scan_timeouts()
    https_url = build_https_url(url)

    try:
        async with httpx.AsyncClient(
            verify=ssl_context_for_scan(),
            follow_redirects=follow_redirects,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(https_url)
            return response
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        return None
    except Exception:
        return None


async def fetch_url(full_url: str, *, follow_redirects: bool = False) -> httpx.Response | None:
    """Effectue un GET vers l'URL complète (pour chemins sensibles, etc.).

    Args:
        full_url: URL complète (ex. https://example.com/.env).
        follow_redirects: Si True, suit les redirections.

    Returns:
        httpx.Response | None: La réponse ou None en cas d'erreur.
    """
    timeouts = get_scan_timeouts()
    try:
        async with httpx.AsyncClient(
            verify=ssl_context_for_scan(),
            follow_redirects=follow_redirects,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(full_url)
            return response
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        return None
    except Exception:
        return None
