"""Helpers pour extraction et construction d'URLs (host, port, build)."""

from urllib.parse import urljoin, urlparse


def extract_host_from_url(url: str) -> str:
    """Extrait le hostname de l'URL (sans port)."""
    parsed = urlparse(url)
    return parsed.hostname or parsed.netloc.split(":")[0]


def extract_port_from_url(url: str) -> int | None:
    """Extrait le port explicite de l'URL."""
    parsed = urlparse(url)
    return parsed.port


def build_url_with_path(base_url: str, path: str) -> str:
    """Construit une URL complète à partir de la base et d'un chemin."""
    base = base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))
