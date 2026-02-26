"""Helpers pour extraction et construction d'URLs (host, port, build http/https)."""

from urllib.parse import urlparse, urlunparse


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
    """Construit l'URL HTTPS à tester à partir de l'URL fournie.

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
