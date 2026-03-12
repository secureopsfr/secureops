"""Pipeline de crawl en streaming SSE : étapes et format des événements.

Émet des événements step (validation, SSRF, robots, crawl) puis result ou error.
Supporte les modes html, playwright et both (exécution parallèle + fusion).
"""

import asyncio
import contextlib
from collections.abc import AsyncGenerator, Callable

from app.config_loader import get_crawler_settings, get_ssrf_settings
from app.services.crawler.executor import execute_crawl_by_mode, make_run_crawler
from app.services.crawler.stream_queue import consume_crawl_queue, error_response_for_exception, put_error_from_exception
from app.services.crawler.types import CrawlMode
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_validator import URLValidationError, validate_and_normalize_url


class QueueProgressCallback:
    """Callback qui envoie les étapes de progression dans une queue SSE."""

    def __init__(self, queue: asyncio.Queue) -> None:
        """Initialise le callback avec la queue SSE."""
        self._queue = queue

    def __call__(self, step: str, message: str) -> None:
        """Émet (step, message) dans la queue (ignore QueueFull)."""
        with contextlib.suppress(asyncio.QueueFull):
            self._queue.put_nowait((step, message))


async def _run_crawl_task(
    queue: asyncio.Queue,
    mode: CrawlMode,
    url: str,
    max_urls: int,
    on_progress: Callable[[str, str], None],
    run_html: Callable,
    run_playwright: Callable,
) -> None:
    """Exécute le crawl selon le mode et envoie les résultats dans la queue."""
    try:
        (
            payload,
            timeout_reached,
            anti_bot_suspected,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            timeout_html,
            timeout_playwright,
            requests_blocked,
            requests_blocked_html,
            requests_blocked_playwright,
            max_consecutive_403,
            disallow_paths,
        ) = await execute_crawl_by_mode(mode, url, max_urls, on_progress, run_html, run_playwright)
        queue.put_nowait(
            (
                "result",
                payload,
                timeout_reached,
                anti_bot_suspected,
                anti_bot_signature_detected,
                anti_bot_low_url_suspected,
                timeout_html,
                timeout_playwright,
                requests_blocked,
                requests_blocked_html,
                requests_blocked_playwright,
                max_consecutive_403,
                disallow_paths,
            )
        )
    except (URLValidationError, Exception) as e:
        put_error_from_exception(e, url, queue)


async def crawl_stream_generator(
    url: str,
    max_urls: int,
    mode: CrawlMode,
) -> AsyncGenerator[str, None]:
    """Générateur SSE : émet un événement à chaque étape du crawl.

    Étapes : validation_url, ssrf, robots (si activé), crawl, puis result ou error.
    Mode both : exécution parallèle des deux crawlers, fusion et déduplication.
    """
    queue: asyncio.Queue[tuple[str, str] | tuple[str, list[dict], bool, bool, bool, bool, bool, bool, bool, bool, int, list[str]]] = asyncio.Queue()
    on_progress = QueueProgressCallback(queue)
    run_html = make_run_crawler(url, max_urls, on_progress, False)
    run_playwright = make_run_crawler(url, max_urls, on_progress, True)

    try:
        yield sse_message("step", {"step": "validation_url_check", "message": "Validation de l'URL…"})
        validated = validate_and_normalize_url(url)
        yield sse_message("step", {"step": "validation_url_done", "message": "URL validée."})

        yield sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (résolution DNS)…"})
        await check_ssrf(validated, timeout=get_ssrf_settings().dns_timeout)
        yield sse_message("step", {"step": "ssrf_done", "message": "Vérification SSRF OK."})

        crawl_task = asyncio.create_task(_run_crawl_task(queue, mode, url, max_urls, on_progress, run_html, run_playwright))
        stream_timeout = get_crawler_settings().stream_timeout_seconds
        async for event in consume_crawl_queue(queue, stream_timeout, crawl_task, sse_message):
            yield event

    except Exception as e:
        msg, code = error_response_for_exception(e, url)
        yield sse_message("error", {"message": msg, "status_code": code})
