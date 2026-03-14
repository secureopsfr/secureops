"""Common preflight helpers shared by single and multi scan flows."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable

from app.config_loader import get_ssrf_settings
from app.utils.sse import sse_message
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url, registered_domain
from app.utils.url_validator import validate_and_normalize_url


async def emit_events(events: list[str]) -> AsyncGenerator[str, None]:
    """Emit a list of SSE chunks in order."""
    for chunk in events:
        yield chunk


def has_error_event(events: list[str]) -> bool:
    """Return True when emitted chunks contain an SSE error event."""
    return any("event: error" in chunk for chunk in events)


async def run_single_preflight(
    *,
    url: str,
    over_global: Callable[[], bool],
    timeout_error_message_factory: Callable[[], str],
) -> tuple[str | None, list[str]]:
    """Validate URL + SSRF checks and emit preflight SSE events."""
    events: list[str] = []
    events.append(sse_message("step", {"step": "validation_url_check", "message": ""}))
    normalized_url = validate_and_normalize_url(url)
    events.append(sse_message("step", {"step": "validation_url_done", "message": ""}))

    if over_global():
        events.append(timeout_error_message_factory())
        return None, events

    events.append(sse_message("step", {"step": "ssrf_check", "message": ""}))
    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    events.append(sse_message("step", {"step": "ssrf_done", "message": ""}))

    if over_global():
        events.append(timeout_error_message_factory())
        return None, events

    events.append(sse_message("step", {"step": "fetch_https_check", "message": ""}))
    return normalized_url, events


async def validate_multi_scan_urls_common(urls: list[str]) -> list[str]:
    """Validate/normalize URLs and enforce single registered-domain + SSRF check."""
    normalized = [validate_and_normalize_url(url) for url in urls]
    reg_domains = {registered_domain(get_scan_base_url(u)) for u in normalized}
    reg_domains.discard("")
    if len(reg_domains) > 1:
        raise ValueError("Toutes les URLs doivent appartenir au même domaine enregistré. " f"Domaines détectés : {', '.join(sorted(reg_domains))}")

    await check_ssrf(normalized[0], timeout=get_ssrf_settings().dns_timeout)
    return normalized
