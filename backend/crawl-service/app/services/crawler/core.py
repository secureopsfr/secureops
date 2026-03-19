"""Noyau du crawler HTTP : fetch, parsing HTML, extraction des liens, BFS.

Roadmap §7.1–7.2 : téléchargement, parsing DOM, extraction liens, suivi des routes,
respect robots.txt, limites (profondeur, max URLs, timeout).
Sitemap : récupéré dès le début (avec robots.txt), injecté dans la file BFS quand elle est vide.
"""

import asyncio
import contextlib
import logging
import time
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config_loader import CrawlerSettings
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse

from common.blacklist import check_blacklist

from app.config_loader import get_blacklist_settings, get_crawler_settings, get_ssrf_settings
from app.services.crawler.anti_bot import detect_anti_bot
from app.services.crawler.url_utils import is_same_domain, normalize_base_domain, normalize_url
from app.services.robots_txt.checks import run_robots_txt_checks
from app.utils.http_fetch import scan_client
from app.utils.ssrf import check_ssrf, is_hostname_blocked
from app.utils.url_helpers import extract_host_from_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


@dataclass
class CrawlUrlEntry:
    """Entrée URL découverte par le crawler."""

    url: str
    depth: int

    def to_dict(self) -> dict:
        """Convertit l'entrée en dict pour la réponse SSE (url, depth)."""
        return {"url": self.url, "depth": self.depth}


@dataclass
class CrawlContext:
    """Contexte partagé préparé avant le crawl (validation, SSRF, settings)."""

    validated: str
    base_origin: str
    base_host: str
    max_urls_limit: int
    crawl_timeout: float
    start_time: float
    settings: "CrawlerSettings"


@dataclass
class PreparedCrawlInputs:
    """Données préparées une seule fois avant exécution d'un ou plusieurs crawlers."""

    context: CrawlContext
    disallow_paths: list[str]
    allow_paths: list[str]
    sitemap_page_urls: list[str]


def _rewrite_url_to_base_host(url: str, base_origin: str) -> str:
    """Réécrit l'URL pour utiliser le même host que l'URL de départ (www ou apex)."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_origin)
    if not parsed.netloc or not base_parsed.netloc:
        return url
    if normalize_base_domain(parsed.netloc) != normalize_base_domain(base_parsed.netloc):
        return url
    return urlunparse(
        (
            parsed.scheme,
            base_parsed.netloc.lower(),
            parsed.path or "/",
            parsed.params,
            parsed.query,
            parsed.fragment or "",
        )
    )


def _has_excluded_extension(url: str, excluded: tuple[str, ...]) -> bool:
    """Vérifie si l'URL se termine par une extension exclue (binaire, assets)."""
    path = urlparse(url).path.lower()
    if not path:
        return False
    return any(path.endswith(ext) for ext in excluded)


def _has_excluded_path_prefix(url: str, prefixes: tuple[str, ...]) -> bool:
    """Vérifie si le chemin de l'URL commence par un préfixe exclu (build artifacts)."""
    path = (urlparse(url).path or "/").lower()
    return any(path.startswith(p.lower()) for p in prefixes)


class _CrawlerHTMLParser(HTMLParser):
    """Parser HTML pour extraire les liens crawlables (a, form, script, link, iframe)."""

    def __init__(self, base_url: str, base_host: str) -> None:
        super().__init__()
        self._base_url = base_url
        self._base_host = base_host
        self._links: list[str] = []

    @property
    def links(self) -> list[str]:
        return self._links

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: C901
        tag_lower = tag.lower()
        attr_map = {name.lower(): (value or "") for name, value in attrs}

        if tag_lower == "a":
            href = attr_map.get("href", "")
            if href:
                self._add_link(href)
        elif tag_lower == "form":
            action = attr_map.get("action", "")
            if action:
                self._add_link(action)
            else:
                self._add_link(self._base_url)
        elif tag_lower == "script":
            src = attr_map.get("src", "")
            if src:
                self._add_link(src)
        elif tag_lower == "link":
            rel = attr_map.get("rel", "").lower()
            href = attr_map.get("href", "")
            if "stylesheet" in rel and href:
                self._add_link(href)
        elif tag_lower == "iframe":
            src = attr_map.get("src", "")
            if src:
                self._add_link(src)

    def _add_link(self, href: str) -> None:
        normalized = normalize_url(href, self._base_url)
        if not normalized:
            return
        if not is_same_domain(normalized, self._base_host):
            return
        self._links.append(normalized)


def _extract_links_from_html(html: str, page_url: str) -> list[str]:
    """Extrait les liens crawlables du HTML."""
    parsed = urlparse(page_url)
    base_host = parsed.netloc.lower()
    parser = _CrawlerHTMLParser(base_url=page_url, base_host=base_host)
    with contextlib.suppress(Exception):
        parser.feed(html)
    seen: set[str] = set()
    result: list[str] = []
    for url in parser.links:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


def _extract_links_html(html: str, page_url: str) -> list[str]:
    """Extrait les URLs des liens du HTML (pour le mode HTTP)."""
    return _extract_links_from_html(html, page_url)


def _is_path_disallowed(path: str, disallow_paths: list[str], allow_paths: list[str]) -> bool:
    """Vérifie si un chemin est interdit par robots.txt."""
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path

    best_disallow_len = -1
    best_allow_len = -1

    for disallow in disallow_paths:
        if not disallow:
            continue
        d = disallow if disallow.startswith("/") else "/" + disallow
        if path.startswith(d) or (d != "/" and path == d.rstrip("/")):
            best_disallow_len = max(best_disallow_len, len(d))

    for allow in allow_paths:
        if not allow:
            continue
        a = allow if allow.startswith("/") else "/" + allow
        if path.startswith(a) or (a != "/" and path == a.rstrip("/")):
            best_allow_len = max(best_allow_len, len(a))

    if best_allow_len >= best_disallow_len and best_allow_len >= 0:
        return False
    return best_disallow_len >= 0


async def fetch_robots_disallow(base_url: str, client) -> tuple[list[str], list[str], list[str]]:
    """Récupère robots.txt et extrait Disallow, Allow et Sitemap."""
    result = await run_robots_txt_checks(base_url, client=client)
    return list(result.disallow_paths), list(result.allow_paths), list(result.sitemap_urls)


async def fetch_robots_and_sitemap(
    base_origin: str,
    base_host: str,
    settings,
    progress: Callable[[str, str], None],
    client,
    start_time: float,
    crawl_timeout: float,
) -> tuple[list[str], list[str], list[str]]:
    """Récupère robots.txt et sitemap (séquence mutualisée HTML / Playwright).

    Returns:
        (disallow_paths, allow_paths, sitemap_page_urls).
    """
    disallow_paths: list[str] = []
    allow_paths: list[str] = []
    sitemap_urls_from_robots: list[str] = []
    if settings.respect_robots_txt:
        progress("robots_check", "")
        disallow_paths, allow_paths, sitemap_urls_from_robots = await fetch_robots_disallow(base_origin.rstrip("/") + "/", client)
        progress("robots_done", "")
    progress("sitemap_check", "")
    sitemap_page_urls = await fetch_all_sitemap_page_urls(
        base_origin,
        base_host,
        sitemap_urls_from_robots,
        disallow_paths,
        allow_paths,
        settings,
        client,
        start_time,
        crawl_timeout,
    )
    progress("sitemap_done", "")
    return disallow_paths, allow_paths, sitemap_page_urls


def _xml_local_name(tag: str) -> str:
    """Retourne le nom local d'une balise XML (sans namespace)."""
    return tag.split("}")[-1] if "}" in tag else tag


def _extract_urls_from_sitemap_xml(content: str) -> tuple[list[str], list[str]]:
    """Extrait les URLs d'un sitemap XML (urlset ou sitemapindex)."""
    page_urls: list[str] = []
    sitemap_urls: list[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return page_urls, sitemap_urls

    root_tag = _xml_local_name(root.tag)
    for elem in root.iter():
        if _xml_local_name(elem.tag) != "loc" or not elem.text or not elem.text.strip():
            continue
        url = elem.text.strip()
        if root_tag == "urlset":
            page_urls.append(url)
        elif root_tag == "sitemapindex":
            sitemap_urls.append(url)
    return page_urls, sitemap_urls


async def fetch_all_sitemap_page_urls(  # noqa: C901
    base_origin: str,
    base_host: str,
    sitemap_urls_from_robots: list[str],
    disallow_paths: list[str],
    allow_paths: list[str],
    settings,
    client,
    start_time: float,
    crawl_timeout: float,
) -> list[str]:
    """Récupère toutes les URLs de pages depuis le sitemap (dès le début du crawl)."""
    fallback_paths = [
        base_origin.rstrip("/") + "/sitemap.xml",
        base_origin.rstrip("/") + "/sitemap_index.xml",
        base_origin.rstrip("/") + "/sitemap-index.xml",
    ]
    urls_to_try = list(sitemap_urls_from_robots) if sitemap_urls_from_robots else []
    for fp in fallback_paths:
        if fp not in urls_to_try:
            urls_to_try.append(fp)
    base_norm = normalize_base_domain(base_host)
    base_origin_parsed = base_origin.rstrip("/")
    all_page_urls: list[str] = []
    seen_sitemap_urls: set[str] = set()

    for sitemap_url in urls_to_try:
        if time.monotonic() - start_time > crawl_timeout:
            break
        if sitemap_url in seen_sitemap_urls:
            continue
        seen_sitemap_urls.add(sitemap_url)
        try:
            resp = await client.get(sitemap_url, headers={"User-Agent": settings.user_agent})
        except Exception as e:
            logger.debug("Erreur fetch sitemap %s : %s", sitemap_url, e)
            continue
        if resp.status_code != 200:
            continue
        ct = (resp.headers.get("content-type") or "").lower()
        body = resp.text if hasattr(resp, "text") else ""
        if "xml" not in ct and not body.lstrip().startswith("<?xml") and "<urlset" not in body and "<sitemapindex" not in body:
            continue

        page_urls, child_sitemap_urls = _extract_urls_from_sitemap_xml(body)

        if not page_urls and child_sitemap_urls:
            for child_url in child_sitemap_urls[: settings.max_child_sitemaps]:
                if time.monotonic() - start_time > crawl_timeout:
                    break
                if child_url in seen_sitemap_urls:
                    continue
                seen_sitemap_urls.add(child_url)
                try:
                    child_resp = await client.get(child_url, headers={"User-Agent": settings.user_agent})
                except Exception:
                    continue
                if child_resp.status_code != 200:
                    continue
                pgs, _ = _extract_urls_from_sitemap_xml(child_resp.text or "")
                page_urls.extend(pgs)

        for url in page_urls:
            url_display = _rewrite_url_to_base_host(url, base_origin_parsed)
            host = extract_host_from_url(url)
            if not host or normalize_base_domain(host) != base_norm:
                continue
            if is_hostname_blocked(host):
                continue
            path = urlparse(url).path or "/"
            if settings.respect_robots_txt and _is_path_disallowed(path, disallow_paths, allow_paths):
                continue
            if _has_excluded_extension(url, settings.excluded_extensions):
                continue
            if _has_excluded_path_prefix(url, settings.excluded_path_prefixes):
                continue
            all_page_urls.append(url_display)

    if all_page_urls:
        logger.info("Sitemap : %d URLs récupérées (injection dans BFS quand file vide)", len(all_page_urls))
    return all_page_urls


async def _fetch_page_html_impl(url: str, client, headers: dict) -> tuple[bool, str | None, int]:
    """Fetch via httpx pour le mode HTML. Retourne (success, html, status_code)."""
    try:
        response = await client.get(url, headers=headers, follow_redirects=True)
        html = ""
        if response.status_code == 200:
            ct = (response.headers.get("content-type") or "").lower()
            if "text/html" in ct:
                with contextlib.suppress(Exception):
                    html = response.text or ""
        return (True, html, response.status_code)
    except Exception as e:
        logger.debug("Erreur fetch %s : %s", url, e)
        return (False, None, 0)


def _make_fetch_page_html(client, headers: dict):
    """Fabrique une fonction fetch_page pour le mode HTML."""
    return lambda url: _fetch_page_html_impl(url, client, headers)


def noop_progress(step: str, message: str = "", **extra) -> None:
    """Callback vide par défaut pour on_progress."""


async def prepare_crawl_context(
    start_url: str,
    max_urls: int | None,
    on_progress: Callable[[str, str], None] | None,
) -> CrawlContext:
    """Prépare le contexte de crawl : validation, SSRF, settings, base_*.

    Returns:
        CrawlContext avec tous les champs communs pour run_crawl et run_crawl_playwright.
    """
    validated = validate_and_normalize_url(start_url)
    await check_blacklist(validated, get_blacklist_settings())
    await check_ssrf(validated, timeout=get_ssrf_settings().dns_timeout)
    settings = get_crawler_settings()
    max_urls_limit = max_urls if max_urls is not None else settings.max_urls
    base_host = extract_host_from_url(validated)
    base_url_parsed = urlparse(validated)
    base_origin = f"{base_url_parsed.scheme}://{base_url_parsed.netloc}"
    crawl_timeout = settings.timeout_seconds
    start_time = time.monotonic()
    return CrawlContext(
        validated=validated,
        base_origin=base_origin,
        base_host=base_host,
        max_urls_limit=max_urls_limit,
        crawl_timeout=crawl_timeout,
        start_time=start_time,
        settings=settings,
    )


def _is_url_skipped(
    url: str,
    depth: int,
    disallow_paths: list[str],
    allow_paths: list[str],
    settings,
    respect_robots: bool,
) -> bool:
    """Vérifie si une URL doit être ignorée (robots, exclusions, profondeur)."""
    path = urlparse(url).path or "/"
    if respect_robots and _is_path_disallowed(path, disallow_paths, allow_paths):
        return True
    if _has_excluded_extension(url, settings.excluded_extensions):
        return True
    if _has_excluded_path_prefix(url, settings.excluded_path_prefixes):
        return True
    if is_hostname_blocked(extract_host_from_url(url)):
        return True
    if depth > settings.max_depth:
        return True
    return False


def _enrich_from_queue_on_403(
    queue: deque,
    base_origin: str,
    disallow_paths: list[str],
    allow_paths: list[str],
    settings,
    sitemap_urls_set: set[str],
    seen_urls: set[str],
    result_entries: list[CrawlUrlEntry],
    max_urls_limit: int,
) -> None:
    """Enrichit result_entries avec les URLs sitemap en attente dans la queue (arrêt 403)."""
    for _ in range(min(len(queue), max_urls_limit - len(result_entries))):
        if not queue:
            break
        url_q, depth_q = queue.popleft()
        url_disp = _rewrite_url_to_base_host(url_q, base_origin)
        if url_disp in seen_urls:
            continue
        if _is_url_skipped(url_q, depth_q, disallow_paths, allow_paths, settings, settings.respect_robots_txt):
            continue
        seen_urls.add(url_disp)
        result_entries.append(CrawlUrlEntry(url=url_disp, depth=depth_q))


async def run_bfs(  # noqa: C901
    validated: str,
    base_origin: str,
    base_host: str,
    disallow_paths: list[str],
    allow_paths: list[str],
    sitemap_page_urls: list[str],
    settings,
    max_urls_limit: int,
    crawl_timeout: float,
    start_time: float,
    progress: Callable[[str, str], None],
    fetch_page: Callable[[str], object],
    extract_links: Callable[[str, str], list[str]],
    log_prefix: str = "",
    stop_event: asyncio.Event | None = None,
) -> tuple[list[CrawlUrlEntry], bool, bool, int, bool]:
    """BFS partagé : parcourt les URLs, fetch + extraction délégués au mode (HTML ou Playwright).

    Args:
        validated: URL de départ.
        base_origin: Origine (scheme + netloc).
        base_host: Host de l'URL de départ.
        disallow_paths: Chemins Disallow (robots.txt).
        allow_paths: Chemins Allow (robots.txt).
        sitemap_page_urls: URLs du sitemap à injecter dans la frontier.
        settings: Config crawler.
        max_urls_limit: Limite d'URLs.
        crawl_timeout: Timeout global (s).
        start_time: Timestamp de début.
        progress: Callback (step, message).
        fetch_page: async (url) -> (success, html|None, status_code).
        extract_links: (html, page_url) -> list[str] d'URLs à ajouter à la queue.
        log_prefix: Préfixe pour les logs (ex. "Playwright").

    Returns:
        (result_entries, timeout_reached, requests_blocked, max_consecutive_403, anti_bot_signature_detected).
    """
    seen_urls: set[str] = set()
    result_entries: list[CrawlUrlEntry] = []
    queue: deque[tuple[str, int]] = deque([(validated, 0)])
    for url_sitemap in sitemap_page_urls:
        queue.append((url_sitemap, 1))
    sitemap_urls_set = set(sitemap_page_urls)
    if sitemap_page_urls:
        logger.info("Frontier %s: %d URLs sitemap ajoutées", log_prefix, len(sitemap_page_urls))

    timeout_reached = False
    requests_blocked = False
    consecutive_403 = 0
    max_consecutive_403 = 0
    anti_bot_signature_detected = False

    while queue and len(seen_urls) < max_urls_limit:
        if stop_event and stop_event.is_set():
            logger.info("Crawl %sarrêt anticipé (autre crawler terminé)", log_prefix)
            break
        if time.monotonic() - start_time > crawl_timeout:
            logger.info("Crawl %stimeout atteint après %d URLs", log_prefix, len(seen_urls))
            timeout_reached = True
            break

        url, depth = queue.popleft()
        url_display = _rewrite_url_to_base_host(url, base_origin)
        if url_display in seen_urls:
            continue
        seen_urls.add(url_display)

        if _is_url_skipped(url, depth, disallow_paths, allow_paths, settings, settings.respect_robots_txt):
            continue

        result_entries.append(CrawlUrlEntry(url=url_display, depth=depth))

        nb = len(result_entries)
        if nb % 10 == 0 or nb <= 3:
            progress("crawl_progress", "", url_count=nb)

        if depth >= settings.max_depth:
            continue

        fetch_result = await fetch_page(url_display)
        success = fetch_result[0]
        html = fetch_result[1] if len(fetch_result) > 1 else None
        status_code = fetch_result[2] if len(fetch_result) > 2 else 0
        links_override = fetch_result[3] if len(fetch_result) > 3 else None

        if not success:
            consecutive_403 = 0
            continue

        if status_code == 403:
            consecutive_403 += 1
            max_consecutive_403 = max(max_consecutive_403, consecutive_403)
            if consecutive_403 >= settings.consecutive_403_threshold:
                logger.info(
                    "Crawl %sarrêté : %d requêtes 403 consécutives (protection anti-bot/WAF)",
                    log_prefix,
                    consecutive_403,
                )
                requests_blocked = True
                _enrich_from_queue_on_403(
                    queue,
                    base_origin,
                    disallow_paths,
                    allow_paths,
                    settings,
                    sitemap_urls_set,
                    seen_urls,
                    result_entries,
                    max_urls_limit,
                )
                break
            continue

        consecutive_403 = 0
        if status_code != 200:
            continue

        if links_override is not None:
            link_urls = links_override
        else:
            max_html = 1024 * 1024
            html_to_parse = (html or "")[:max_html] if html else ""
            if html_to_parse and detect_anti_bot(
                html_to_parse,
                settings.anti_bot_indicators,
            ):
                anti_bot_signature_detected = True
            link_urls = extract_links(html_to_parse, url_display)
        if not link_urls and not html:
            continue

        for link_url in link_urls:
            if link_url in seen_urls or len(seen_urls) + len(queue) >= max_urls_limit:
                continue
            if _has_excluded_extension(link_url, settings.excluded_extensions):
                continue
            if _has_excluded_path_prefix(link_url, settings.excluded_path_prefixes):
                continue
            queue.append((link_url, depth + 1))

    result_entries.sort(key=lambda e: (e.depth, e.url))
    return (
        result_entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected,
    )


async def run_crawl(
    start_url: str,
    max_urls: int | None = None,
    on_progress: Callable[[str, str], None] | None = None,
    stop_event: asyncio.Event | None = None,
) -> tuple[list[CrawlUrlEntry], bool, bool, int, bool, list[str]]:
    """Exécute un crawl synchrone depuis l'URL de départ.

    Returns:
        Tuple (
            liste CrawlUrlEntry,
            timeout_reached,
            requests_blocked,
            max_consecutive_403,
            anti_bot_signature_detected,
            disallow_paths,
        ).

    Raises:
        URLValidationError: Si l'URL est invalide.
    """
    prepared = await prepare_crawl_inputs(start_url, max_urls=max_urls, on_progress=on_progress)
    return await run_crawl_from_prepared(prepared, on_progress=on_progress, stop_event=stop_event)


async def prepare_crawl_inputs(
    start_url: str,
    *,
    max_urls: int | None = None,
    on_progress: Callable[[str, str], None] | None = None,
) -> PreparedCrawlInputs:
    """Prépare le contexte, robots.txt et sitemap pour un ou plusieurs crawlers."""
    progress = on_progress or noop_progress
    ctx = await prepare_crawl_context(start_url, max_urls, on_progress)
    async with scan_client() as client:
        disallow_paths, allow_paths, sitemap_page_urls = await fetch_robots_and_sitemap(
            ctx.base_origin, ctx.base_host, ctx.settings, progress, client, ctx.start_time, ctx.crawl_timeout
        )
    return PreparedCrawlInputs(
        context=ctx,
        disallow_paths=disallow_paths,
        allow_paths=allow_paths,
        sitemap_page_urls=sitemap_page_urls,
    )


async def run_crawl_from_prepared(
    prepared: PreparedCrawlInputs,
    *,
    on_progress: Callable[[str, str], None] | None = None,
    stop_event: asyncio.Event | None = None,
) -> tuple[list[CrawlUrlEntry], bool, bool, int, bool, list[str]]:
    """Exécute le crawl HTML depuis un contexte déjà préparé."""
    progress = on_progress or noop_progress
    ctx = prepared.context
    async with scan_client() as client:
        headers = {"User-Agent": ctx.settings.user_agent}
        fetch_page_html = _make_fetch_page_html(client, headers)
        (
            result_entries,
            timeout_reached,
            requests_blocked,
            max_consecutive_403,
            anti_bot_signature_detected,
        ) = await run_bfs(
            ctx.validated,
            ctx.base_origin,
            ctx.base_host,
            prepared.disallow_paths,
            prepared.allow_paths,
            prepared.sitemap_page_urls,
            ctx.settings,
            ctx.max_urls_limit,
            ctx.crawl_timeout,
            ctx.start_time,
            progress,
            fetch_page=fetch_page_html,
            extract_links=_extract_links_html,
            stop_event=stop_event,
        )
    return (
        result_entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected,
        prepared.disallow_paths,
    )
