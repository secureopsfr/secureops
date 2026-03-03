"""Vérification Sitemap (roadmap §5.1.6bis).

Vérifie la présence de Sitemap: dans robots.txt, fallback à l'emplacement classique,
et analyse le contenu du sitemap pour détecter des URLs sensibles exposées.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlparse

from app.config_loader import get_robots_txt_settings
from app.utils.http_fetch import get_with_client
from app.utils.url_helpers import build_url_with_path

# Chemins classiques pour le fallback si Sitemap: absent.
_SITEMAP_FALLBACK_PATHS = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")


@dataclass
class SensitiveSitemapUrl:
    """URL du sitemap identifiée comme sensible.

    Attributes:
        url (str): URL complète extraite du sitemap.
        path (str): Chemin extrait de l'URL.
        pattern (str): Motif qui a déclenché la détection.
        severity (str): info, low, medium, high, critical.
    """

    url: str
    path: str
    pattern: str
    severity: str


@dataclass
class SitemapCheckResult:
    """Résultat de la vérification sitemap.

    Attributes:
        sitemap_found (bool): True si un sitemap a été trouvé (déclaré ou fallback).
        sitemap_undeclared (bool): True si trouvé via fallback (non déclaré dans robots.txt).
        sensitive_urls (tuple[SensitiveSitemapUrl, ...]): URLs sensibles détectées.
        fetch_ok (bool): True si au moins une requête a abouti.
    """

    sitemap_found: bool
    sitemap_undeclared: bool
    sensitive_urls: tuple[SensitiveSitemapUrl, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        sensitive_serialized = [{"url": s.url, "path": s.path, "pattern": s.pattern, "severity": s.severity} for s in self.sensitive_urls]
        return {
            "sitemap_found": self.sitemap_found,
            "sitemap_undeclared": self.sitemap_undeclared,
            "sensitive_urls": sensitive_serialized,
            "fetch_ok": self.fetch_ok,
        }


def _url_path_matches_sensitive(url: str, patterns: tuple[tuple[str, str], ...]) -> SensitiveSitemapUrl | None:
    """Vérifie si le chemin de l'URL correspond à un motif sensible.

    Args:
        url: URL complète (ex. https://example.com/admin/dashboard).
        patterns: Tuple de (motif, severity). Motif = sous-chaîne à rechercher (insensible casse).

    Returns:
        SensitiveSitemapUrl si match, None sinon.
    """
    parsed = urlparse(url)
    path = parsed.path or "/"
    path_lower = path.lower()
    for pattern, severity in patterns:
        if pattern not in path_lower or (pattern == "api" and "public" in path_lower):
            continue
        return SensitiveSitemapUrl(url=url, path=path, pattern=pattern, severity=severity)
    return None


def _extract_urls_from_sitemap_xml(content: str) -> list[str]:
    """Extrait les URLs <loc> du contenu XML sitemap.

    Gère le namespace sitemaps.org (urlset) et sitemap index (sitemapindex).
    Utilise iter() pour gérer les namespaces (local name 'loc').

    Args:
        content: Contenu brut du sitemap XML.

    Returns:
        list[str]: Liste des URLs extraites.
    """
    urls: list[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return urls

    def local_name(tag: str) -> str:
        """Retourne le nom local (sans namespace)."""
        return tag.split("}")[-1] if "}" in tag else tag

    for elem in root.iter():
        if local_name(elem.tag) == "loc" and elem.text and elem.text.strip():
            urls.append(elem.text.strip())

    return urls


def _resolve_sitemap_urls(base_url: str, robots_txt_result) -> tuple[list[str], bool]:
    """Détermine les URLs à tester pour le sitemap et si le fallback est utilisé.

    Returns:
        tuple[list[str], bool]: (urls à tester, sitemap_undeclared).
    """
    sitemap_urls = getattr(robots_txt_result, "sitemap_urls", None) if robots_txt_result else None
    if sitemap_urls:
        return list(sitemap_urls), False
    return [build_url_with_path(base_url, p) for p in _SITEMAP_FALLBACK_PATHS], True


def _is_sitemap_xml_response(response) -> bool:
    """Vérifie si la réponse est un sitemap XML valide."""
    if response.status_code != 200:
        return False
    ct = response.headers.get("content-type", "").lower()
    body = response.text.strip()
    return "xml" in ct or body.startswith("<?xml") or "<urlset" in body or "<sitemapindex" in body


def _analyze_sitemap_urls(content: str) -> list[SensitiveSitemapUrl]:
    """Analyse le contenu XML et retourne les URLs sensibles détectées."""
    urls = _extract_urls_from_sitemap_xml(content)
    patterns = get_robots_txt_settings()
    sensitive: list[SensitiveSitemapUrl] = []
    for url in urls:
        if re.search(r"/sitemap[_-]?\d*\.xml", url, re.IGNORECASE):
            continue
        match = _url_path_matches_sensitive(url, patterns)
        if match is not None:
            sensitive.append(match)
    return sensitive


async def run_sitemap_checks(
    base_url: str,
    *,
    robots_txt_result,
    client,
) -> SitemapCheckResult:
    """Vérifie le sitemap : Sitemap: dans robots.txt, fallback, analyse URLs sensibles.

    Args:
        base_url: URL de base (ex. https://example.com/).
        robots_txt_result: Résultat de run_robots_txt_checks (pour sitemap_urls).
        client: Client httpx (issu de scan_client()).

    Returns:
        SitemapCheckResult: Sitemap trouvé, URLs sensibles, etc.
    """
    urls_to_try, sitemap_undeclared = _resolve_sitemap_urls(base_url, robots_txt_result)
    content: str | None = None
    fetch_ok = False

    for sitemap_url in urls_to_try:
        response = await get_with_client(client, sitemap_url, follow_redirects=False)
        if response is None:
            continue
        fetch_ok = True
        if _is_sitemap_xml_response(response):
            content = response.text
            break

    if not content:
        return SitemapCheckResult(
            sitemap_found=False,
            sitemap_undeclared=False,
            sensitive_urls=(),
            fetch_ok=fetch_ok,
        )

    sensitive = _analyze_sitemap_urls(content)
    return SitemapCheckResult(
        sitemap_found=True,
        sitemap_undeclared=sitemap_undeclared,
        sensitive_urls=tuple(sensitive),
        fetch_ok=True,
    )
