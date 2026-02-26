"""Exécution du scan : étapes métier (TLS, etc.). Utilise get_scan_timeouts pour le client HTTP."""

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx

from app.config_loader import get_scan_timeouts


@dataclass
class TlsCheckResult:
    """Résultat des vérifications TLS/HTTPS.

    Attributes:
        https_enabled (bool): True si le site répond en HTTPS.
        http_redirects_to_https (bool | None): True si HTTP redirige vers HTTPS, False sinon.
            None si non vérifiable (HTTP inaccessible ou HTTPS non activé).
        findings (tuple[str, ...]): Liste des findings.
    """

    https_enabled: bool
    http_redirects_to_https: bool | None
    findings: tuple[str, ...]


def _build_https_url(url: str) -> str:
    """Construit l'URL HTTPS à tester à partir de l'URL fournie.

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL https://host/ (port 443 implicite).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    return urlunparse(("https", host, "/", "", "", ""))


def _build_http_url(url: str) -> str:
    """Construit l'URL HTTP à tester (pour la vérification redirection).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL http://host/ (port 80 implicite).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    return urlunparse(("http", host, "/", "", "", ""))


def _location_redirects_to_https(location: str | None) -> bool:
    """Vérifie si l'en-tête Location pointe vers https://.

    Args:
        location: Valeur de l'en-tête Location.

    Returns:
        bool: True si Location commence par https:// (insensible à la casse).
    """
    if not location or not isinstance(location, str):
        return False
    return location.strip().lower().startswith("https://")


async def run_tls_checks(url: str) -> TlsCheckResult:
    """Vérifications TLS/HTTPS (roadmap §3.1).

    Vérification 1 : HTTPS activé ? Une requête GET vers https://<host>/ doit aboutir
    (même si le certificat est invalide ou auto-signé). Si connexion refusée ou timeout,
    HTTPS n'est pas proposé.

    Args:
        url: URL normalisée à scanner (sera utilisée pour extraire le host).

    Returns:
        TlsCheckResult: https_enabled et liste des findings.
    """
    timeouts = get_scan_timeouts()
    https_url = _build_https_url(url)
    findings: list[str] = []

    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(
                timeouts.connection,
                read=timeouts.read,
            ),
        ) as client:
            response = await client.get(https_url)
            # Toute réponse (200, 301, 404, etc.) indique que HTTPS répond
            _ = response.status_code
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        findings.append("HTTPS non activé (connexion refusée ou timeout). Risque d'interception.")
        return TlsCheckResult(https_enabled=False, http_redirects_to_https=None, findings=tuple(findings))
    except Exception as e:
        findings.append(f"HTTPS non activé : {e!s}")
        return TlsCheckResult(https_enabled=False, http_redirects_to_https=None, findings=tuple(findings))

    # Vérification 2 : Redirection HTTP→HTTPS (uniquement si HTTPS activé)
    http_redirects_to_https: bool | None = None
    http_url = _build_http_url(url)
    try:
        async with httpx.AsyncClient(
            verify=False,
            follow_redirects=False,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(http_url)
            if response.status_code in (301, 302, 307, 308):
                location = response.headers.get("location")
                http_redirects_to_https = _location_redirects_to_https(location)
                if not http_redirects_to_https:
                    findings.append("Pas de redirection HTTP→HTTPS : la redirection ne pointe pas vers https://.")
            else:
                http_redirects_to_https = False
                findings.append("Pas de redirection HTTP→HTTPS (réponse 200 ou autre sans redirection). " "Le trafic peut rester en clair.")
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        http_redirects_to_https = None
        # HTTP inaccessible : non vérifiable (site peut être HTTPS-only)
    except Exception:
        http_redirects_to_https = None

    return TlsCheckResult(https_enabled=True, http_redirects_to_https=http_redirects_to_https, findings=tuple(findings))
