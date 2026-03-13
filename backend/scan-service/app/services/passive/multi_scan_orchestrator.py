"""Passive multi-URL orchestration built on generic pipeline base."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config_loader import get_multi_scan_settings, get_ssrf_settings
from app.models.multi_scan import MultiScanResult, PageScanResult
from app.services.passive._page_checks_runner import run_page_checks
from app.services.passive._scan_core import FindingsBundle, build_findings_bundle
from app.services.passive.cors_cross_origin.checks import run_cors_domain_checks
from app.services.passive.directory_listing import run_directory_listing_checks
from app.services.passive.exposed_files import run_exposed_files_checks
from app.services.passive.robots_txt import run_robots_txt_checks
from app.services.passive.sitemap import run_sitemap_checks
from app.services.passive.tls import run_tls_checks
from app.services.pipelines.multi_scan_base import BaseMultiScanOrchestrator, MultiScanExecutionSettings, OnProgress
from app.utils.http_fetch import get_with_client_or_error, http_request_category, log_http_metrics, scan_client
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url, registered_domain
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


class PassiveMultiScanOrchestrator(BaseMultiScanOrchestrator):
    """Passive implementation using the reusable multi-scan template."""

    def __init__(self, *, on_progress: OnProgress = None) -> None:
        """Initialize passive orchestration and shared per-run asset cache."""
        super().__init__(on_progress=on_progress)
        self._assets_cache: dict[str, str | None] = {}

    def resolve_base_url(self, urls: list[str]) -> str:
        """Resolve canonical base URL from the first validated target URL."""
        normalized_first = validate_and_normalize_url(urls[0])
        return get_scan_base_url(normalized_first)

    def get_execution_settings(self) -> MultiScanExecutionSettings:
        """Load passive multi-scan concurrency and timeout settings."""
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
        """Publish passive multi-scan HTTP metrics once execution completes."""
        log_http_metrics(client, "multi-scan", base_url=base_url, urls=len(urls))

    async def run_domain_phase(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        """Run domain-level passive checks once and share results across pages."""
        domain_results: dict[str, Any] = {}
        await asyncio.gather(
            self._run_domain_tls(base_url, client, domain_results),
            self._run_domain_robots_then_sitemap(base_url, client, domain_results),
            self._run_domain_exposed_files(base_url, client, domain_results),
            self._run_domain_directory_listing(base_url, client, domain_results),
            self._run_domain_cors(base_url, client, domain_results),
        )
        await self.emit_progress("domain_checks_done")
        return domain_results

    async def _run_domain_robots_then_sitemap(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
    ) -> None:
        await self.emit_progress("domain_robots_check")
        with http_request_category("robots_txt"):
            domain_results["robots_txt"] = await run_robots_txt_checks(base_url, client=client)
        await self.emit_progress("domain_sitemap_check")
        with http_request_category("sitemap"):
            domain_results["sitemap"] = await run_sitemap_checks(
                base_url,
                robots_txt_result=domain_results["robots_txt"],
                client=client,
            )

    async def _run_domain_tls(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
    ) -> None:
        await self.emit_progress("domain_tls_check")
        normalized = validate_and_normalize_url(base_url)
        with http_request_category("tls"):
            fetch_result = await get_with_client_or_error(client, base_url, follow_redirects=True)
            https_response = fetch_result.response if fetch_result.success else None
            domain_results["tls"] = await run_tls_checks(
                normalized,
                https_response=https_response,
                client=client,
            )

    async def _run_domain_exposed_files(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
    ) -> None:
        await self.emit_progress("domain_exposed_files_check")
        with http_request_category("exposed_files"):
            domain_results["exposed_files"] = await run_exposed_files_checks(base_url, client=client)

    async def _run_domain_directory_listing(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
    ) -> None:
        await self.emit_progress("domain_directory_listing_check")
        with http_request_category("directory_listing"):
            domain_results["directory_listing"] = await run_directory_listing_checks(base_url, client=client)

    async def _run_domain_cors(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        domain_results: dict[str, Any],
    ) -> None:
        await self.emit_progress("domain_cors_check")
        with http_request_category("cors_cross_origin"):
            domain_results["cors_domain"] = await run_cors_domain_checks(base_url, client=client)

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
        """Run passive checks for one page and merge with domain-level findings."""
        await self.emit_progress(
            "page_scan_started",
            url=url,
            page_index=page_index + 1,
            total_pages=total_pages,
        )
        try:
            with http_request_category("initial_fetch"):
                response = await asyncio.wait_for(
                    client.get(url, follow_redirects=True),
                    timeout=page_timeout,
                )
        except Exception as exc:
            logger.warning("multi_scan: page inaccessible url=%s err=%s", url, exc)
            await self.emit_progress("page_scan_error", url=url)
            return self._build_error_page_result(url, str(exc), domain_results)

        tls_result = domain_results.get("tls")
        is_https = getattr(tls_result, "https_enabled", True)
        page_check_results = await run_page_checks(
            response,
            url,
            client,
            assets_cache=self._assets_cache,
            is_https=is_https,
            domain_cors_result=domain_results.get("cors_domain"),
        )

        merged: dict[str, Any] = {k: v for k, v in domain_results.items() if k != "cors_domain"}
        merged.update(page_check_results)
        bundle: FindingsBundle = build_findings_bundle(merged)

        await self.emit_progress("page_scan_done", url=url)
        return PageScanResult(
            url=url,
            score=bundle.score,
            findings=[f.to_dict() for f in bundle.findings],
            category_summaries=bundle.category_summaries,
            total_tests_count=bundle.total_tests_count,
        )

    def _build_error_page_result(
        self,
        url: str,
        error_message: str,
        domain_results: dict[str, Any],
    ) -> PageScanResult:
        domain_only: dict[str, Any] = {k: v for k, v in domain_results.items() if k != "cors_domain"}
        bundle: FindingsBundle = build_findings_bundle(domain_only)
        return PageScanResult(
            url=url,
            score=bundle.score,
            findings=[f.to_dict() for f in bundle.findings],
            category_summaries=bundle.category_summaries,
            error=error_message,
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
        """Build the final passive multi-scan payload object."""
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
    """Public passive multi-scan entrypoint."""
    orchestrator = PassiveMultiScanOrchestrator(on_progress=on_progress)
    return await orchestrator.run(urls)


async def validate_multi_scan_urls(urls: list[str]) -> list[str]:
    """Validate/normalize URLs and enforce single registered-domain + SSRF check."""
    from app.utils.url_validator import URLValidationError  # noqa: F401

    normalized: list[str] = []
    for url in urls:
        normalized.append(validate_and_normalize_url(url))

    reg_domains = {registered_domain(get_scan_base_url(u)) for u in normalized}
    reg_domains.discard("")
    if len(reg_domains) > 1:
        raise ValueError(f"Toutes les URLs doivent appartenir au même domaine enregistré. " f"Domaines détectés : {', '.join(sorted(reg_domains))}")

    await check_ssrf(normalized[0], timeout=get_ssrf_settings().dns_timeout)
    return normalized
