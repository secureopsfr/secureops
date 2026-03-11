"""Re-export des helpers URL depuis common + helpers locaux."""

from urllib.parse import urlparse

import tldextract
from common.url_helpers import (
    build_http_url,
    build_https_url,
    build_url_with_path,
    extract_host_from_url,
    extract_port_from_url,
    get_host_from_url,
    get_https_port_from_url,
    get_scan_base_url,
    location_redirects_to_https,
)

# Instance qui utilise uniquement le snapshot intégré (pas de fetch réseau,
# pas de cache disque). Suffit pour tous les TLDs courants (la liste est
# régulièrement mise à jour lors des releases de la lib).
_tld_extract = tldextract.TLDExtract(
    suffix_list_urls=(),  # Désactive le fetch réseau
    fallback_to_snapshot=True,
    cache_dir=None,
)


def registered_domain(url_or_netloc: str) -> str:
    """Retourne le domaine enregistré (eTLD+1) d'une URL ou d'un netloc.

    Utilise tldextract pour gérer correctement les TLDs composés (.co.uk, .com.br…).

    Exemples :
        registered_domain("https://blog.example.com/")       → "example.com"
        registered_domain("www.example.com")                 → "example.com"
        registered_domain("example.com")                     → "example.com"
        registered_domain("https://api.example.co.uk/path")  → "example.co.uk"

    Args:
        url_or_netloc: URL complète ou netloc brut.

    Returns:
        str: Domaine enregistré (eTLD+1), ou chaîne vide si non déterminable.
    """
    netloc = urlparse(url_or_netloc).netloc or url_or_netloc
    # Retire le port éventuel (ex. example.com:8080 → example.com)
    host = netloc.split(":")[0]
    ext = _tld_extract(host)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    # Fallback : hôte brut (IP, localhost, etc.)
    return host


__all__ = [
    "build_http_url",
    "build_https_url",
    "build_url_with_path",
    "extract_host_from_url",
    "extract_port_from_url",
    "get_host_from_url",
    "get_https_port_from_url",
    "get_scan_base_url",
    "location_redirects_to_https",
    "registered_domain",
]
