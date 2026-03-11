"""Exécution métier d'un job scan async."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import parse_sse_chunk, utc_now

from app.services.scan_stream import scan_stream_generator


async def execute_scan_job(
    *,
    url: str,
    scan_type: str,
    input_json: dict[str, Any] | None = None,
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Exécute un job de scan et retourne (result, error)."""
    if scan_type in {"backend", "custom"}:
        fake_result = {
            "url": url,
            "timestamp": utc_now().isoformat(),
            "duration": 0.1,
            "score": 100,
            "findings": [],
            "status": "success",
            "scan_type": scan_type,
            "message": f"Fake {scan_type} scan result (V1).",
        }
        if on_progress:
            await on_progress("fake_scan_done", f"Fake {scan_type} scan généré.")
        return fake_result, None

    result_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    async for chunk in scan_stream_generator(url, authorization=None):
        parsed = parse_sse_chunk(chunk)
        if not parsed:
            continue
        event, data = parsed
        if event == "step" and isinstance(data, dict):
            step = str(data.get("step", "step"))
            message = str(data.get("message", ""))
            anomaly_count_raw = data.get("anomaly_count")
            anomaly_count = int(anomaly_count_raw) if isinstance(anomaly_count_raw, int) else None
            if on_progress:
                if anomaly_count is None:
                    await on_progress(step, message)
                else:
                    await on_progress(step, message, anomaly_count=anomaly_count)
        elif event == "result" and isinstance(data, dict):
            result_payload = data
        elif event == "error" and isinstance(data, dict):
            error_payload = data

    return result_payload, error_payload
