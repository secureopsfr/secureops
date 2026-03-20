"""Destructive multi-URL orchestration based on reusable pipeline base."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config_loader import get_multi_scan_settings
from app.models.finding import Finding
from app.models.multi_scan import MultiScanResult, PageScanResult
from app.services.destructive._fake_security_checks import DESTRUCTIVE_STEPS
from app.services.mode_category_summaries import build_destructive_category_summaries, count_total_tests
from app.services.pipelines.multi_scan_base import BaseMultiScanOrchestrator, MultiScanExecutionSettings, OnProgress
from app.services.scan_preflight_common import validate_multi_scan_urls_common
from app.services.scoring import compute_score
from app.utils.http_fetch import get_with_client_or_error, log_http_metrics, scan_client
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


class DestructiveMultiScanOrchestrator(BaseMultiScanOrchestrator):
    """Destructive implementation using the reusable multi-scan template."""

    def resolve_base_url(self, urls: list[str]) -> str:
        """Resolve canonical base URL from the first validated target URL."""
        normalized_first = validate_and_normalize_url(urls[0])
        return get_scan_base_url(normalized_first)

    def get_execution_settings(self) -> MultiScanExecutionSettings:
        """Provide runtime settings (timeouts/concurrency) for this pipeline."""
        settings = get_multi_scan_settings()
        return MultiScanExecutionSettings(
            concurrent_pages=settings.concurrent_pages,
            page_timeout=settings.page_timeout,
        )

    def get_client_context(self):
        """Provide the shared HTTP client context for the full run."""
        return scan_client()

    async def after_client_run(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str,
        urls: list[str],
    ) -> None:
        """Publish destructive multi-scan HTTP metrics once execution completes."""
        log_http_metrics(client, "destructive-multi-scan", base_url=base_url, urls=len(urls))

    async def run_domain_phase(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        """Run domain-level destructive checks and return reusable intermediate results."""
        _ = client
        await self.emit_progress("domain_checks_done", url=base_url)
        return {"domain_findings": []}

    async def run_single_page(
        self,
        *,
        url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
        page_timeout: float,
        page_index: int,
        total_pages: int,
    ) -> PageScanResult:
        """Run destructive checks for one page and return its page-level result object."""
        await self.emit_progress(
            "page_scan_started",
            url=url,
            page_index=page_index + 1,
            total_pages=total_pages,
        )

        try:
            fetch_result = await asyncio.wait_for(
                get_with_client_or_error(client, url, follow_redirects=True),
                timeout=page_timeout,
            )
        except Exception as exc:
            logger.warning("destructive_multi_scan: page inaccessible url=%s err=%s", url, exc)
            await self.emit_progress("page_scan_error", url=url)
            return PageScanResult(url=url, score=0, findings=[], error="Page inaccessible for destructive checks")

        if not fetch_result.success:
            await self.emit_progress("page_scan_error", url=url)
            return PageScanResult(url=url, score=0, findings=[], error="Page inaccessible for destructive checks")

        findings: list[Finding] = list(domain_results.get("domain_findings", []))
        for step_name, step_fn in DESTRUCTIVE_STEPS:
            await self.emit_progress(f"{step_name}_check", url=url)
            result = step_fn(url)
            findings.extend(result.findings)
            await self.emit_progress(f"{step_name}_done", url=url, anomaly_count=len(result.findings))

        await self.emit_progress("page_scan_done", url=url)
        summaries = build_destructive_category_summaries(findings)
        return PageScanResult(
            url=url,
            score=compute_score(findings),
            findings=[f.to_dict() for f in findings],
            category_summaries=summaries,
            total_tests_count=count_total_tests(summaries),
        )

    def build_final_result(
        self,
        *,
        base_url: str,
        urls: list[str],
        page_results: list[PageScanResult],
        score_global: int,
        timestamp: str,
        duration: float,
    ) -> MultiScanResult:
        """Build and return the final aggregate destructive multi-scan result."""
        return MultiScanResult(
            base_url=base_url,
            urls=urls,
            score_global=score_global,
            page_results=page_results,
            timestamp=timestamp,
            duration=duration,
        )


async def run_multi_scan(
    urls: list[str],
    on_progress: OnProgress = None,
) -> MultiScanResult:
    """Execute a destructive multi-URL scan with shared orchestration logic."""
    orchestrator = DestructiveMultiScanOrchestrator(on_progress=on_progress)
    return await orchestrator.run(urls)


async def validate_multi_scan_urls(urls: list[str]) -> list[str]:
    """Validate destructive multi-scan targets with shared preflight rules."""
    return await validate_multi_scan_urls_common(urls)
