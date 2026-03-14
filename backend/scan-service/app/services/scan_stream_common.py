"""Shared helpers for scan stream modules."""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from app.errors.fetch_errors import build_unexpected_error_payload, build_validation_error_payload
from app.services.scan_history_save import save_scan_to_history
from app.utils.sse import sse_message
from app.utils.url_validator import URLValidationError

ErrorHook = Callable[[Exception], None | Awaitable[None]]
PipelineFactory = Callable[[], AsyncGenerator[str, None]]


async def emit_save_events(
    *,
    payload: dict[str, Any],
    authorization: str | None,
    logger: Any,
    mode_label: str,
) -> AsyncGenerator[str, None]:
    """Emit optional history save events for authenticated users."""
    if not authorization:
        return
    try:
        scan_id = await save_scan_to_history(payload, authorization)
        if scan_id:
            yield sse_message("save_done", {"scan_id": scan_id})
    except Exception as exc:
        logger.warning("%s history save failed: %s", mode_label, exc)
        yield sse_message("save_failed", {"message": str(exc)})


async def _run_hook(hook: ErrorHook | None, exc: Exception) -> None:
    if hook is None:
        return
    maybe_result = hook(exc)
    if inspect.isawaitable(maybe_result):
        await maybe_result


async def stream_with_standard_error_events(
    *,
    pipeline_factory: PipelineFactory,
    on_validation_error: ErrorHook | None = None,
    on_unexpected_error: ErrorHook | None = None,
) -> AsyncGenerator[str, None]:
    """Run a stream pipeline and normalize validation/unexpected errors to SSE."""
    try:
        async for chunk in pipeline_factory():
            yield chunk
    except URLValidationError as exc:
        await _run_hook(on_validation_error, exc)
        yield sse_message("error", build_validation_error_payload(str(exc)))
    except Exception as exc:
        await _run_hook(on_unexpected_error, exc)
        yield sse_message("error", build_unexpected_error_payload(str(exc)))
