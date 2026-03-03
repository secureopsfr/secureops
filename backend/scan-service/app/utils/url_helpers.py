"""Helpers pour extraction et construction d'URLs (host, port, build http/https).

Inclut aussi la construction de l'URL de base utilisée pour le scan principal.
En production, on force systématiquement une URL HTTPS canonique. En
environnement non prod, on garde l'URL d'origine pour les cas localhost /
127.0.0.1 avec port explicite afin de faciliter les tests locaux.
"""

import os
from urllib.parse import urljoin, urlparse, urlunparse


def _is_prod_env() -> bool:
    """Indique si l'environnement est en mode production.

    La variable d'environnement IS_PROD est considérée vraie si elle vaut
    "1", "true" ou "yes" (insensible à la casse). Si elle est absente,
    le comportement par défaut est conservateur (prod).

    Returns:
        bool: True si l'environnement est considéré comme production.
    """
    value = os.getenv("IS_PROD", "true").lower().strip()
    return value in ("1", "true", "yes")


def extract_host_from_url(url: str) -> str:
    """Extrait le hostname de l'URL (sans port).

    Args:
        url: URL à parser (ex. https://example.com:443/path).

    Returns:
        str: Hostname (ex. example.com). Utilise netloc si hostname absent.
    """
    parsed = urlparse(url)
    return parsed.hostname or parsed.netloc.split(":")[0]


def extract_port_from_url(url: str) -> int | None:
    """Extrait le port explicite de l'URL.

    Args:
        url: URL à parser.

    Returns:
        int | None: Port si présent dans l'URL, None sinon.
    """
    parsed = urlparse(url)
    return parsed.port


def build_https_url(url: str) -> str:
    """Construit l'URL HTTPS canonique à tester à partir de l'URL fournie.

    Préserve le port explicite non standard pour HTTPS (ex. badssl.com:1010 pour tests TLS 1.0).
    Pour http://host:80, produit https://host/ (port 443 implicite).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL https://host[:port]/ (port 443 implicite si absent ou standard).
    """
    host = extract_host_from_url(url)
    # Port non-443 uniquement si l'URL source est https avec port explicite
    port = extract_port_from_url(url) if (urlparse(url).scheme or "").lower() == "https" else None
    netloc = f"{host}:{port}" if port is not None and port != 443 else host
    return urlunparse(("https", netloc, "/", "", "", ""))


def build_http_url(url: str) -> str:
    """Construit l'URL HTTP à tester (pour la vérification redirection).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL http://host/ (port 80 implicite).
    """
    host = extract_host_from_url(url)
    return urlunparse(("http", host, "/", "", "", ""))


def get_host_from_url(url: str) -> str:
    """Extrait le hostname de l'URL (alias de extract_host_from_url)."""
    return extract_host_from_url(url)


def get_https_port_from_url(url: str) -> int:
    """Extrait le port HTTPS de l'URL (443 par défaut si absent ou si http)."""
    parsed = urlparse(url)
    if (parsed.scheme or "").lower() == "https":
        port = extract_port_from_url(url)
        if port is not None:
            return port
    return 443


def get_scan_base_url(url: str) -> str:
    """Construit l'URL de base utilisée pour le scan principal.

    En production (`IS_PROD=true`), on utilise toujours l'URL HTTPS canonique
    (upgrade éventuel depuis http → https, port 443 par défaut).

    En environnement non prod (`IS_PROD=false`), pour les URLs locales de test
    (localhost ou 127.0.0.1 avec port explicite), on conserve l'URL d'origine
    afin d'éviter un upgrade vers https://host/ sur le port 443 qui échouerait
    (cas typique d'un petit serveur HTTP de test sur 127.0.0.1:8001).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL de base à utiliser pour le fetch principal.
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    host = extract_host_from_url(url)
    port = extract_port_from_url(url)

    if not _is_prod_env() and scheme == "http" and port is not None and host in ("127.0.0.1", "localhost"):
        return url

    return build_https_url(url)


def build_url_with_path(base_url: str, path: str) -> str:
    """Construit une URL complète à partir de la base et d'un chemin.

    Args:
        base_url: URL de base (ex. https://example.com/).
        path: Chemin à joindre (ex. .env, .git/config).

    Returns:
        str: URL complète (ex. https://example.com/.env).
    """
    base = base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def location_redirects_to_https(location: str | None) -> bool:
    """Vérifie si l'en-tête Location pointe vers https://.

    Args:
        location: Valeur de l'en-tête Location.

    Returns:
        bool: True si Location commence par https:// (insensible à la casse).
    """
    if not location or not isinstance(location, str):
        return False
    return location.strip().lower().startswith("https://")
