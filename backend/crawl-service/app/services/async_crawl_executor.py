"""Exécution métier d'un job crawl async."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import parse_sse_chunk, utc_now

from app.services.crawler.crawl_stream import crawl_stream_generator


async def execute_crawl_job(
    *,
    url: str,
    scan_type: str,
    input_json: dict[str, Any] | None = None,
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Exécute un job crawl et retourne (result, error)."""
    params = input_json or {}

    if scan_type in {"backend", "custom"}:
        fake_result = {
            "urls": [{"url": url, "depth": 0}],
            "timeout_reached": False,
            "anti_bot_suspected": False,
            "anti_bot_signature_detected": False,
            "anti_bot_low_url_suspected": False,
            "timeout_html": False,
            "timeout_playwright": False,
            "requests_blocked": False,
            "requests_blocked_html": False,
            "requests_blocked_playwright": False,
            "max_consecutive_403": 0,
            "disallow_paths": [],
            "message": f"Fake {scan_type} crawl result (V1).",
            "generated_at": utc_now().isoformat(),
        }
        if on_progress:
            await on_progress("fake_crawl_done", f"Fake {scan_type} crawl généré.")
        return fake_result, None

    max_urls = int(params.get("max_urls", 50))
    mode = str(params.get("mode", "html"))
    result_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None

    async for chunk in crawl_stream_generator(url=url, max_urls=max_urls, mode=mode):  # type: ignore[arg-type]
        parsed = parse_sse_chunk(chunk)
        if not parsed:
            continue
        event, data = parsed
        if event == "step" and isinstance(data, dict):
            if on_progress:
                step = str(data.get("step", "step"))
                message = str(data.get("message", ""))
                extra = {k: v for k, v in data.items() if k not in ("step", "message")}
                await on_progress(step, message, **extra)
        elif event == "result" and isinstance(data, dict):
            result_payload = data
        elif event == "error" and isinstance(data, dict):
            error_payload = data
    return result_payload, error_payload
