"""Fake custom multi-scan orchestrator (multi URL)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import utc_now

from app.services.mode_category_summaries import build_custom_category_summaries, count_total_tests

OnProgress = Callable[..., Awaitable[None]] | None


async def run_multi_scan(
    *,
    urls: list[str],
    scan_type: str,
    on_progress: OnProgress = None,
) -> dict[str, Any]:
    """Return a fake custom multi-scan payload."""
    if on_progress:
        await on_progress("custom_multi_plan_check", "Simulation custom multi-URL initialisée.")
        await on_progress("custom_multi_plan_done", "Aucun scénario custom exécuté (mode fake).")

    category_summaries = build_custom_category_summaries()
    total_tests_count = count_total_tests(category_summaries)
    page_results = [
        {
            "url": url,
            "score": 100,
            "findings": [],
            "category_summaries": category_summaries,
            "total_tests_count": total_tests_count,
        }
        for url in urls
    ]
    return {
        "result_mode": "multi",
        "base_url": urls[0] if urls else "",
        "urls": urls,
        "score_global": 100,
        "page_results": page_results,
        "timestamp": utc_now().isoformat(),
        "duration": 0.1,
        "scan_type": scan_type,
        "scan_mode": "custom",
        "status": "success",
        "message": "Fake custom multi scan result (V1).",
    }
