"""Gestion des pages Playwright : navigation, extraction des liens, détection anti-bot."""

import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.services.crawler.anti_bot import detect_anti_bot
from app.services.crawler.constants import EXTRACT_LINKS_JS

if TYPE_CHECKING:
    from app.services.crawler.core import CrawlContext
from app.services.crawler.core import CrawlUrlEntry, run_bfs
from app.services.crawler.url_utils import is_same_domain, normalize_url

logger = logging.getLogger(__name__)


class AntiBotFlag:
    """Conteneur mutable pour le flag anti-bot (utilisé dans une closure async)."""

    def __init__(self) -> None:
        """Initialise le flag anti-bot."""
        self.detected = False


def extract_normalized_links(raw_links: list, page_url: str, base_host: str) -> list[str]:
    """Convertit les liens bruts Playwright en URLs normalisées du même domaine.

    Args:
        raw_links: Liste de dict avec 'url' ou 'href'.
        page_url: URL de la page courante.
        base_host: Host de l'URL de départ.

    Returns:
        URLs normalisées du même domaine.
    """
    links = []
    for item in raw_links:
        link_url = item.get("url") or item.get("href")
        if not link_url:
            continue
        normalized = normalize_url(link_url, page_url)
        if normalized and is_same_domain(normalized, base_host):
            links.append(normalized)
    return links


async def fetch_page_playwright(
    page,
    url: str,
    ctx: "CrawlContext",
    anti_bot_flag: AntiBotFlag,
    page_timeout_ms: int,
    network_idle_ms: int,
) -> tuple[bool, str | None, int, list[str] | None]:
    """Navigue et extrait les liens d'une page Playwright.

    Args:
        page: Instance Page Playwright.
        url: URL à charger.
        ctx: CrawlContext (settings, base_host).
        anti_bot_flag: Flag mutable pour la détection anti-bot.
        page_timeout_ms: Timeout navigation (ms).
        network_idle_ms: Timeout networkidle (ms).

    Returns:
        (success, html_content, status_code, links).
    """
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=page_timeout_ms)
        status = response.status if response else 0
        if status == 403:
            return (True, None, 403, None)
        if status >= 400:
            return (True, None, status, None)
        await page.wait_for_load_state("networkidle", timeout=network_idle_ms)
        html_content = ""
        try:
            html_content = await page.content()
            if detect_anti_bot(html_content, ctx.settings.anti_bot_indicators):
                anti_bot_flag.detected = True
                logger.info("Protection anti-bot détectée sur %s", url)
        except Exception:
            pass
        raw_links = await page.evaluate(EXTRACT_LINKS_JS)
        links = extract_normalized_links(raw_links, url, ctx.base_host)
        return (True, html_content, 200, links)
    except Exception as e:
        logger.warning("Erreur navigation Playwright %s : %s", url, e)
        return (False, None, 0, None)


def _extract_links_dummy(_html: str, _page_url: str) -> list[str]:
    """Extracteur de liens factice pour le BFS Playwright (les liens viennent du DOM)."""
    return []


async def _playwright_fetch_page_impl(
    context,
    ctx: "CrawlContext",
    anti_bot_flag: AntiBotFlag,
    page_timeout_ms: int,
    network_idle_ms: int,
    url: str,
):
    """Implémentation du fetch Playwright : ouvre une page, charge l'URL, retourne le résultat."""
    page = await context.new_page()
    try:
        return await fetch_page_playwright(page, url, ctx, anti_bot_flag, page_timeout_ms, network_idle_ms)
    finally:
        await page.close()


def _make_playwright_fetch_page(
    context,
    ctx: "CrawlContext",
    anti_bot_flag: AntiBotFlag,
    page_timeout_ms: int,
    network_idle_ms: int,
):
    """Fabrique une fonction fetch_page pour le BFS Playwright."""
    return lambda url: _playwright_fetch_page_impl(context, ctx, anti_bot_flag, page_timeout_ms, network_idle_ms, url)


async def run_playwright_browser_bfs(
    ctx: "CrawlContext",
    disallow_paths: list[str],
    allow_paths: list[str],
    sitemap_page_urls: list[str],
    progress: Callable[[str, str], None],
    stop_event: asyncio.Event | None,
    anti_bot_flag: AntiBotFlag,
    page_timeout_ms: int,
    network_idle_ms: int,
) -> tuple[list[CrawlUrlEntry], bool, bool]:
    """Lance Playwright, exécute le BFS et retourne (entries, timeout, blocked).

    Args:
        ctx: CrawlContext préparé.
        disallow_paths: Chemins Disallow (robots.txt).
        allow_paths: Chemins Allow (robots.txt).
        sitemap_page_urls: URLs du sitemap.
        progress: Callback (step, message).
        stop_event: Event d'arrêt anticipé.
        anti_bot_flag: Flag mutable anti-bot.
        page_timeout_ms: Timeout page (ms).
        network_idle_ms: Timeout networkidle (ms).

    Returns:
        (entries, timeout_reached, requests_blocked).
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(
            user_agent=ctx.settings.user_agent,
            ignore_https_errors=True,
            java_script_enabled=True,
        )
        context.set_default_timeout(page_timeout_ms)
        context.set_default_navigation_timeout(page_timeout_ms)
        fetch_page = _make_playwright_fetch_page(context, ctx, anti_bot_flag, page_timeout_ms, network_idle_ms)
        return await run_bfs(
            ctx.validated,
            ctx.base_origin,
            ctx.base_host,
            disallow_paths,
            allow_paths,
            sitemap_page_urls,
            ctx.settings,
            ctx.max_urls_limit,
            ctx.crawl_timeout,
            ctx.start_time,
            progress,
            fetch_page=fetch_page,
            extract_links=_extract_links_dummy,
            log_prefix="Playwright ",
            stop_event=stop_event,
        )
