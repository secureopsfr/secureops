"""Utilitaires URL partagés par les crawlers HTML et Playwright."""

from urllib.parse import urljoin, urlparse, urlunparse

from app.utils.url_helpers import extract_host_from_url


def normalize_url(url: str, base_url: str) -> str | None:
    """Normalise une URL relative ou absolue.

    Args:
        url: URL à normaliser (peut être relative).
        base_url: URL de base pour résoudre les relatives.

    Returns:
        URL absolue normalisée ou None si invalide.
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    if url.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
        return None
    try:
        absolute = urljoin(base_url, url)
    except Exception:
        return None
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", parsed.params, parsed.query, ""))


def normalize_base_domain(host: str) -> str:
    """Retourne le domaine de base (sans préfixe www.) pour comparaison.

    Args:
        host: Hostname (ex. www.example.com).

    Returns:
        Domaine normalisé (ex. example.com).
    """
    h = host.lower().strip()
    if h.startswith("www.") and len(h) > 4:
        return h[4:]
    return h


def is_same_domain(url: str, base_host: str) -> bool:
    """Vérifie si l'URL appartient au même domaine (ou sous-domaine).

    Args:
        url: URL à vérifier.
        base_host: Host de l'URL de départ.

    Returns:
        True si même domaine.
    """
    host = extract_host_from_url(url)
    if not host:
        return False
    base_norm = normalize_base_domain(base_host)
    host_norm = normalize_base_domain(host)
    return host_norm == base_norm or host_norm.endswith("." + base_norm)
