"""Module de fetch HTTP partagé pour le scan.

Centralise la requête HTTPS (SSL permissif, timeouts) afin d'éviter les appels
dupliqués entre TLS et Security Headers.
"""

import ssl

import httpx

from app.config_loader import get_scan_timeouts
from app.utils.url_helpers import build_https_url


def _ssl_context_for_scan() -> ssl.SSLContext:
    """Contexte SSL permissif pour le scan : TLS 1.0+ accepté, pas de vérif. certificat.

    Returns:
        ssl.SSLContext: Contexte configuré.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx


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
            verify=_ssl_context_for_scan(),
            follow_redirects=follow_redirects,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(https_url)
            return response
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        return None
    except Exception:
        return None
