"""Shared payload/result helpers for intrusive scans."""

from __future__ import annotations

import time

from app.models.finding import Finding
from app.models.scan_result import ScanResult
from app.services.mode_category_summaries import build_intrusive_category_summaries, count_total_tests
from app.services.scoring import compute_score


def build_result_payload(url: str, findings: list[Finding], start_time: float) -> dict:
    """Build final intrusive payload aligned with passive response shape."""
    duration = time.monotonic() - start_time
    result = ScanResult(
        url=url,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        duration=duration,
        score=compute_score(findings),
        findings=tuple(findings),
    )
    payload = result.to_dict()
    payload["status"] = "success"
    payload["category_summaries"] = build_intrusive_category_summaries(findings)
    payload["total_tests_count"] = count_total_tests(payload["category_summaries"])
    return payload
