"""Intrusive scan execution returning a JSON payload."""

from __future__ import annotations

import logging
import time

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.errors.fetch_errors import build_sse_error_payload
from app.models.finding import Finding
from app.services.intrusive._fake_security_checks import INTRUSIVE_STEPS
from app.services.intrusive._scan_core import build_result_payload
from app.utils.http_fetch import get_with_client_or_error, log_http_metrics, scan_client
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


class ScanRunError(Exception):
    """Execution error for intrusive scan runner."""

    def __init__(self, message: str, status_code: int = 500):
        """Store error details associated with a scan execution failure."""
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def run_scan_to_result(url: str) -> dict:
    """Run intrusive pipeline and return a passive-compatible payload."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    normalized_url = validate_and_normalize_url(url)
    if _over_global():
        raise ScanRunError("Timeout global dépassé", status_code=408)

    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)
    if _over_global():
        raise ScanRunError("Timeout global dépassé", status_code=408)

    https_url = get_scan_base_url(normalized_url)
    findings: list[Finding] = []

    async with scan_client() as client:
        try:
            fetch_result = await get_with_client_or_error(client, https_url, follow_redirects=True)
            if not fetch_result.success:
                payload = build_sse_error_payload(fetch_result)
                raise ScanRunError(
                    payload.get("message", "Site inaccessible"),
                    status_code=payload.get("status_code", 503),
                )

            for _, step_fn in INTRUSIVE_STEPS:
                if _over_global():
                    raise ScanRunError("Timeout global dépassé", status_code=408)
                findings.extend(step_fn(normalized_url).findings)
        finally:
            log_http_metrics(client, "intrusive-scan-runner", url=https_url)

    return build_result_payload(normalized_url, findings, start)
