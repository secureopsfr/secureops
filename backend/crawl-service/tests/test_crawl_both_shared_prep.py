"""Tests du mode both avec préparation mutualisée."""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from app.services.crawler.core import CrawlUrlEntry
from app.services.crawler.executor import execute_crawl_by_mode


@dataclass
class _FakePrepared:
    marker: str = "shared"


def test_execute_crawl_by_mode_both_prepares_once_and_shares_context() -> None:
    """Mode both mutualise la préparation robots/sitemap et partage le contexte."""
    prepared = _FakePrepared()
    mock_prepare = AsyncMock(return_value=prepared)
    mock_html = AsyncMock(return_value=([], False, False, ["disallow-html"]))
    mock_playwright = AsyncMock(return_value=([], False, True, False, ["disallow-playwright"]))

    async def _run() -> tuple[list[dict], bool, bool, bool, list[str]]:
        return await execute_crawl_by_mode(
            mode="both",
            url="https://example.com",
            max_urls=50,
            on_progress=lambda _step, _message: None,
            run_html_fn=AsyncMock(),
            run_playwright_fn=AsyncMock(),
        )

    with (
        patch("app.services.crawler.executor.crawl_core.prepare_crawl_inputs", mock_prepare),
        patch("app.services.crawler.executor.crawl_core.run_crawl_from_prepared", mock_html),
        patch("app.services.crawler.executor.run_crawl_playwright_from_prepared", mock_playwright),
    ):
        payload, timeout_reached, anti_bot_suspected, requests_blocked, disallow_paths = asyncio.run(_run())

    assert payload == []
    assert timeout_reached is False
    # When both tasks complete at the same time, the current branch prefers HTML first.
    assert anti_bot_suspected is False
    assert requests_blocked is False
    assert disallow_paths == ["disallow-html"]
    assert mock_prepare.await_count == 1

    html_args, html_kwargs = mock_html.await_args
    playwright_args, playwright_kwargs = mock_playwright.await_args
    assert html_args[0] is prepared
    assert playwright_args[0] is prepared
    assert html_kwargs.get("stop_event") is not None
    assert playwright_kwargs.get("stop_event") is html_kwargs.get("stop_event")


def test_both_stops_other_only_when_first_reaches_url_limit() -> None:
    """Le stop_event est activé seulement si le premier crawler atteint max_urls."""
    prepared = _FakePrepared()
    mock_prepare = AsyncMock(return_value=prepared)
    html_entries = [
        CrawlUrlEntry(url="https://example.com/a", type="page", depth=0),
        CrawlUrlEntry(url="https://example.com/b", type="page", depth=0),
    ]
    mock_html = AsyncMock(return_value=(html_entries, False, False, ["disallow-html"]))

    async def _slow_playwright(_prepared, *, on_progress, stop_event):  # noqa: ARG001
        await asyncio.sleep(0.01)
        return ([], False, False, False, [])

    mock_playwright = AsyncMock(side_effect=_slow_playwright)

    async def _run() -> None:
        await execute_crawl_by_mode(
            mode="both",
            url="https://example.com",
            max_urls=2,
            on_progress=lambda _step, _message: None,
            run_html_fn=AsyncMock(),
            run_playwright_fn=AsyncMock(),
        )

    with (
        patch("app.services.crawler.executor.crawl_core.prepare_crawl_inputs", mock_prepare),
        patch("app.services.crawler.executor.crawl_core.run_crawl_from_prepared", mock_html),
        patch("app.services.crawler.executor.run_crawl_playwright_from_prepared", mock_playwright),
    ):
        asyncio.run(_run())

    stop_event = mock_playwright.await_args.kwargs["stop_event"]
    assert stop_event.is_set() is True
