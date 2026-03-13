"""Fake destructive scan runner (single URL)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import utc_now

from app.services.mode_category_summaries import build_destructive_category_summaries, count_total_tests


async def run_scan_to_result(
    *,
    url: str,
    scan_type: str,
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """Return a fake destructive single-scan payload."""
    if on_progress:
        await on_progress("destructive_plan_check", "Simulation destructive initialisée.")
        await on_progress("destructive_plan_done", "Aucune action destructive exécutée (mode fake).")
    category_summaries = build_destructive_category_summaries()
    return {
        "url": url,
        "timestamp": utc_now().isoformat(),
        "duration": 0.1,
        "score": 100,
        "findings": [],
        "category_summaries": category_summaries,
        "total_tests_count": count_total_tests(category_summaries),
        "status": "success",
        "scan_type": scan_type,
        "scan_mode": "destructive",
        "message": "Fake destructive scan result (V1).",
    }
