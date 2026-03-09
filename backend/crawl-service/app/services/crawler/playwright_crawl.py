"""Crawl SPA via Playwright : exécution JavaScript pour extraire les liens.

Utilisé quand l'utilisateur indique que le site est une SPA (case à cocher).
"""

import asyncio
import logging
import time
from collections.abc import Callable

from app.services.crawler.core import CrawlUrlEntry, fetch_robots_and_sitemap, noop_progress, prepare_crawl_context
from app.services.crawler.playwright_page import AntiBotFlag, run_playwright_browser_bfs
from app.utils.http_fetch import scan_client

logger = logging.getLogger(__name__)


async def run_crawl_playwright(
    start_url: str,
    max_urls: int | None = None,
    on_progress: Callable[[str, str], None] | None = None,
    stop_event: asyncio.Event | None = None,
) -> tuple[list[CrawlUrlEntry], bool, bool, bool, list[str]]:
    """Crawl SPA via Playwright : exécute le JavaScript pour découvrir les liens.

    Returns:
        Tuple (liste CrawlUrlEntry, timeout_reached, anti_bot_suspected, requests_blocked, disallow_paths).

    Raises:
        URLValidationError: Si l'URL est invalide.
        ImportError: Si Playwright n'est pas installé.
    """
    progress = on_progress or noop_progress
    try:
        import playwright.async_api  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Playwright n'est pas installé. Exécutez: pip install playwright && playwright install chromium",
        ) from e

    ctx = await prepare_crawl_context(start_url, max_urls, on_progress)

    logger.info(
        "Crawl Playwright démarré : host=%s max_urls=%d timeout=%ds",
        ctx.base_host,
        ctx.max_urls_limit,
        int(ctx.crawl_timeout),
    )

    async with scan_client() as client:
        disallow_paths, allow_paths, sitemap_page_urls = await fetch_robots_and_sitemap(
            ctx.base_origin, ctx.base_host, ctx.settings, progress, client, ctx.start_time, ctx.crawl_timeout
        )

    anti_bot_flag = AntiBotFlag()
    result_entries, timeout_reached, requests_blocked = await run_playwright_browser_bfs(
        ctx,
        disallow_paths,
        allow_paths,
        sitemap_page_urls,
        progress,
        stop_event,
        anti_bot_flag,
        ctx.settings.playwright_page_timeout_ms,
        ctx.settings.playwright_network_idle_timeout_ms,
    )

    anti_bot_suspected = anti_bot_flag.detected
    elapsed = time.monotonic() - ctx.start_time

    if len(result_entries) <= 3 and not anti_bot_suspected:
        anti_bot_suspected = True
        logger.info("Crawl Playwright : peu d'URLs (%d), anti-bot suspecté", len(result_entries))

    logger.info(
        "Crawl Playwright terminé : %d URLs en %.1fs timeout=%s anti_bot=%s requests_blocked=%s",
        len(result_entries),
        elapsed,
        timeout_reached,
        anti_bot_suspected,
        requests_blocked,
    )
    return result_entries, timeout_reached, anti_bot_suspected, requests_blocked, disallow_paths
