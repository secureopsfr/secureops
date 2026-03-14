"""Intrusive scan SSE pipeline (initial fake probes)."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Callable

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.errors.fetch_errors import build_sse_error_payload, build_timeout_global_error_payload
from app.models.finding import Finding
from app.services.intrusive._fake_security_checks import INTRUSIVE_STEPS
from app.services.intrusive._scan_core import build_result_payload
from app.services.scan_stream_common import emit_save_events, stream_with_standard_error_events
from app.utils.http_fetch import get_with_client_or_error, log_http_metrics, scan_client
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


def _timeout_error_message() -> str:
    return sse_message("error", build_timeout_global_error_payload())


async def _emit_events(events: list[str]) -> AsyncGenerator[str, None]:
    """Emit a list of SSE chunks in order."""
    for chunk in events:
        yield chunk


def _has_error_event(events: list[str]) -> bool:
    """Return True when emitted chunks contain an SSE error event."""
    return any("event: error" in chunk for chunk in events)


async def _perform_preflight(url: str, over_global: Callable[[], bool]) -> tuple[str | None, list[str]]:
    """Validate URL and run SSRF checks before intrusive probes."""
    events: list[str] = []
    events.append(sse_message("step", {"step": "validation_url_check", "message": ""}))
    normalized_url = validate_and_normalize_url(url)
    events.append(sse_message("step", {"step": "validation_url_done", "message": ""}))

    if over_global():
        events.append(_timeout_error_message())
        return None, events

    events.append(sse_message("step", {"step": "ssrf_check", "message": ""}))
    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    events.append(sse_message("step", {"step": "ssrf_done", "message": ""}))

    if over_global():
        events.append(_timeout_error_message())
        return None, events

    events.append(sse_message("step", {"step": "fetch_https_check", "message": ""}))
    return normalized_url, events


async def _perform_intrusive_checks(
    normalized_url: str,
    over_global: Callable[[], bool],
) -> tuple[list[Finding], list[str], bool]:
    """Fetch target and execute intrusive fake probes."""
    https_url = get_scan_base_url(normalized_url)
    findings: list[Finding] = []
    events: list[str] = []

    async with scan_client() as client:
        try:
            fetch_result = await get_with_client_or_error(client, https_url, follow_redirects=True)
            if not fetch_result.success:
                events.append(sse_message("error", build_sse_error_payload(fetch_result)))
                return findings, events, True

            events.append(sse_message("step", {"step": "fetch_https_done", "message": ""}))

            for step_name, step_fn in INTRUSIVE_STEPS:
                if over_global():
                    events.append(_timeout_error_message())
                    return findings, events, True
                events.append(sse_message("step", {"step": f"{step_name}_check", "message": ""}))
                result = step_fn(normalized_url)
                findings.extend(result.findings)
                events.append(
                    sse_message(
                        "step",
                        {
                            "step": f"{step_name}_done",
                            "message": "",
                            "anomaly_count": len(result.findings),
                        },
                    )
                )
        finally:
            log_http_metrics(client, "intrusive-scan-stream", url=https_url)

    return findings, events, False


async def _run_pipeline_steps(url: str, authorization: str | None = None) -> AsyncGenerator[str, None]:
    """Execute intrusive scan flow and emit SSE chunks for each stage."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    normalized_url, preflight_events = await _perform_preflight(url, _over_global)
    async for chunk in _emit_events(preflight_events):
        yield chunk
    if _has_error_event(preflight_events):
        return

    if normalized_url is None:
        return

    findings, check_events, should_stop = await _perform_intrusive_checks(normalized_url, _over_global)
    async for chunk in _emit_events(check_events):
        yield chunk
    if should_stop:
        return

    payload = build_result_payload(normalized_url, findings, start)
    yield sse_message("result", payload)
    async for chunk in emit_save_events(
        payload=payload,
        authorization=authorization,
        logger=logger,
        mode_label="Intrusive",
    ):
        yield chunk


async def scan_stream_generator(url: str, authorization: str | None = None) -> AsyncGenerator[str, None]:
    """Stream intrusive scan progress and result through SSE chunks."""
    async for chunk in stream_with_standard_error_events(
        pipeline_factory=lambda: _run_pipeline_steps(url, authorization=authorization),
    ):
        yield chunk
