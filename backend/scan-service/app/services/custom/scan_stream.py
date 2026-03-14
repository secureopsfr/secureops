"""Custom scan SSE stream wrapper."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.services.custom.scan_runner import run_scan_to_result
from app.services.scan_stream_common import emit_save_events, stream_with_standard_error_events
from app.utils.sse import sse_message

logger = logging.getLogger(__name__)


async def _run_pipeline_steps(
    url: str,
    scan_type: str,
    authorization: str | None = None,
) -> AsyncGenerator[str, None]:
    """Run custom scan and emit step/result events as SSE chunks."""
    step_events: list[str] = []

    async def _capture_progress(step: str, message: str, **extra: Any) -> None:
        data = {"step": step, "message": message, **extra}
        step_events.append(sse_message("step", data))

    payload = await run_scan_to_result(
        url=url,
        scan_type=scan_type,
        on_progress=_capture_progress,
    )

    for chunk in step_events:
        yield chunk

    yield sse_message("result", payload)

    async for chunk in emit_save_events(
        payload=payload,
        authorization=authorization,
        logger=logger,
        mode_label="Custom",
    ):
        yield chunk


async def scan_stream_generator(
    url: str,
    authorization: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream custom scan progress and final result through SSE chunks."""
    async for chunk in stream_with_standard_error_events(
        pipeline_factory=lambda: _run_pipeline_steps(
            url=url,
            scan_type="frontend",
            authorization=authorization,
        ),
    ):
        yield chunk
