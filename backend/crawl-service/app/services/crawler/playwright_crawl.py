"""Crawl SPA via Playwright : exécution JavaScript pour extraire les liens.

Utilisé quand l'utilisateur indique que le site est une SPA (case à cocher).
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.services.crawler import core as crawl_core
from app.services.crawler.playwright_page import AntiBotFlag, run_playwright_browser_bfs

if TYPE_CHECKING:
    from app.services.crawler.core import CrawlUrlEntry, PreparedCrawlInputs

logger = logging.getLogger(__name__)


async def run_crawl_playwright(
    start_url: str,
    max_urls: int | None = None,
    on_progress: Callable[[str, str], None] | None = None,
    stop_event: asyncio.Event | None = None,
) -> tuple[list["CrawlUrlEntry"], bool, bool, bool, bool, bool, int, list[str]]:
    """Crawl SPA via Playwright : exécute le JavaScript pour découvrir les liens.

    Returns:
        Tuple (
            liste CrawlUrlEntry,
            timeout_reached,
            anti_bot_suspected,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            requests_blocked,
            max_consecutive_403,
            disallow_paths,
        ).

    Raises:
        URLValidationError: Si l'URL est invalide.
        ImportError: Si Playwright n'est pas installé.
    """
    progress = on_progress or crawl_core.noop_progress
    try:
        import playwright.async_api  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Playwright n'est pas installé. Exécutez: pip install playwright && playwright install chromium",
        ) from e

    if hasattr(crawl_core, "prepare_crawl_inputs"):
        prepared = await crawl_core.prepare_crawl_inputs(start_url, max_urls=max_urls, on_progress=progress)
        return await run_crawl_playwright_from_prepared(prepared, on_progress=progress, stop_event=stop_event)

    # Compat mode for mixed runtime versions (old core loaded in some processes).
    ctx = await crawl_core.prepare_crawl_context(start_url, max_urls, on_progress)
    async with crawl_core.scan_client() as client:
        disallow_paths, allow_paths, sitemap_page_urls = await crawl_core.fetch_robots_and_sitemap(
            ctx.base_origin, ctx.base_host, ctx.settings, progress, client, ctx.start_time, ctx.crawl_timeout
        )
    anti_bot_flag = AntiBotFlag()
    (
        result_entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected_bfs,
    ) = await run_playwright_browser_bfs(
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
    anti_bot_signature_detected = anti_bot_flag.detected or anti_bot_signature_detected_bfs
    anti_bot_suspected = anti_bot_signature_detected
    anti_bot_low_url_suspected = False
    elapsed = time.monotonic() - ctx.start_time
    if len(result_entries) <= 3 and not anti_bot_suspected:
        anti_bot_suspected = True
        anti_bot_low_url_suspected = True
        logger.info("Crawl Playwright : peu d'URLs (%d), anti-bot suspecté", len(result_entries))
    logger.info(
        "Crawl Playwright terminé : %d URLs en %.1fs timeout=%s anti_bot=%s requests_blocked=%s",
        len(result_entries),
        elapsed,
        timeout_reached,
        anti_bot_suspected,
        requests_blocked,
    )
    return (
        result_entries,
        timeout_reached,
        anti_bot_suspected,
        anti_bot_signature_detected,
        anti_bot_low_url_suspected,
        requests_blocked,
        max_consecutive_403,
        disallow_paths,
    )


async def run_crawl_playwright_from_prepared(
    prepared: "PreparedCrawlInputs",
    *,
    on_progress: Callable[[str, str], None] | None = None,
    stop_event: asyncio.Event | None = None,
) -> tuple[list["CrawlUrlEntry"], bool, bool, bool, bool, bool, int, list[str]]:
    """Exécute le crawl Playwright depuis un contexte déjà préparé."""
    progress = on_progress or crawl_core.noop_progress
    try:
        import playwright.async_api  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Playwright n'est pas installé. Exécutez: pip install playwright && playwright install chromium",
        ) from e

    ctx = prepared.context
    logger.info(
        "Crawl Playwright démarré : host=%s max_urls=%d timeout=%ds",
        ctx.base_host,
        ctx.max_urls_limit,
        int(ctx.crawl_timeout),
    )
    anti_bot_flag = AntiBotFlag()
    (
        result_entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected_bfs,
    ) = await run_playwright_browser_bfs(
        ctx,
        prepared.disallow_paths,
        prepared.allow_paths,
        prepared.sitemap_page_urls,
        progress,
        stop_event,
        anti_bot_flag,
        ctx.settings.playwright_page_timeout_ms,
        ctx.settings.playwright_network_idle_timeout_ms,
    )
    anti_bot_signature_detected = anti_bot_flag.detected or anti_bot_signature_detected_bfs
    anti_bot_suspected = anti_bot_signature_detected
    anti_bot_low_url_suspected = False
    elapsed = time.monotonic() - ctx.start_time
    if len(result_entries) <= 3 and not anti_bot_suspected:
        anti_bot_suspected = True
        anti_bot_low_url_suspected = True
        logger.info("Crawl Playwright : peu d'URLs (%d), anti-bot suspecté", len(result_entries))
    logger.info(
        "Crawl Playwright terminé : %d URLs en %.1fs timeout=%s anti_bot=%s requests_blocked=%s",
        len(result_entries),
        elapsed,
        timeout_reached,
        anti_bot_suspected,
        requests_blocked,
    )
    return (
        result_entries,
        timeout_reached,
        anti_bot_suspected,
        anti_bot_signature_detected,
        anti_bot_low_url_suspected,
        requests_blocked,
        max_consecutive_403,
        prepared.disallow_paths,
    )
