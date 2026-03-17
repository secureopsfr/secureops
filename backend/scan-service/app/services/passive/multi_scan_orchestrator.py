"""Passive multi-URL orchestration built on generic pipeline base."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config_loader import get_multi_scan_settings
from app.models.multi_scan import MultiScanResult, PageScanResult
from app.services.passive._page_checks_runner import run_page_checks
from app.services.passive._scan_core import FindingsBundle, build_findings_bundle
from app.services.passive.backend.api import run_api_checks
from app.services.passive.both.cors_cross_origin.checks import run_cors_domain_checks
from app.services.passive.both.directory_listing import run_directory_listing_checks
from app.services.passive.both.exposed_files import run_exposed_files_checks
from app.services.passive.both.tls import run_tls_checks
from app.services.passive.frontend.robots_txt import run_robots_txt_checks
from app.services.passive.frontend.sitemap import run_sitemap_checks
from app.services.pipelines.multi_scan_base import BaseMultiScanOrchestrator, MultiScanExecutionSettings, OnProgress
from app.services.scan_preflight_common import validate_multi_scan_urls_common
from app.utils.http_fetch import get_with_client_or_error, http_request_category, log_http_metrics, scan_client
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


class PassiveMultiScanOrchestrator(BaseMultiScanOrchestrator):
    """Passive implementation using the reusable multi-scan template."""

    def __init__(
        self,
        *,
        on_progress: OnProgress = None,
        scan_type: str = "frontend",
    ) -> None:
        """Initialize passive orchestration and shared per-run caches."""
        super().__init__(on_progress=on_progress)
        self._scan_type = scan_type
        self._assets_cache: dict[str, str | None] = {}
        # Cache du bundle domaine : évite de re-normaliser/re-scorer N fois
        # pour les pages en erreur (toutes partagent le même résultat domaine).
        self._domain_bundle_cache: FindingsBundle | None = None

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
        """Run domain-level passive checks once and share results across pages.

        Chaque coroutine retourne un dict partiel qui est fusionné après gather,
        ce qui élimine la mutation concurrente d'un dict partagé.
        robots_txt et sitemap sont ignorés pour scan_type=backend.
        """
        tasks = [
            self._run_domain_tls(base_url, client),
            self._run_domain_exposed_files(base_url, client),
            self._run_domain_directory_listing(base_url, client),
            self._run_domain_cors(base_url, client),
            self._run_domain_api(base_url, client),
        ]
        if self._scan_type != "backend":
            tasks.insert(1, self._run_domain_robots_then_sitemap(base_url, client))
        partial_results = await asyncio.gather(*tasks)
        domain_results: dict[str, Any] = {}
        for partial in partial_results:
            domain_results.update(partial)
        await self.emit_progress("domain_checks_done")
        return domain_results

    async def _run_domain_robots_then_sitemap(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_robots_check")
        with http_request_category("robots_txt"):
            robots_result = await run_robots_txt_checks(base_url, client=client)
        await self.emit_progress("domain_sitemap_check")
        with http_request_category("sitemap"):
            sitemap_result = await run_sitemap_checks(
                base_url,
                robots_txt_result=robots_result,
                client=client,
            )
        return {"robots_txt": robots_result, "sitemap": sitemap_result}

    async def _run_domain_tls(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_tls_check")
        normalized = validate_and_normalize_url(base_url)
        with http_request_category("tls"):
            fetch_result = await get_with_client_or_error(client, base_url, follow_redirects=True)
            https_response = fetch_result.response if fetch_result.success else None
            tls_result = await run_tls_checks(
                normalized,
                https_response=https_response,
                client=client,
            )
        return {"tls": tls_result}

    async def _run_domain_exposed_files(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_exposed_files_check")
        with http_request_category("exposed_files"):
            result = await run_exposed_files_checks(base_url, client=client)
        return {"exposed_files": result}

    async def _run_domain_directory_listing(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_directory_listing_check")
        with http_request_category("directory_listing"):
            result = await run_directory_listing_checks(base_url, client=client)
        return {"directory_listing": result}

    async def _run_domain_cors(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_cors_check")
        with http_request_category("cors_cross_origin"):
            result = await run_cors_domain_checks(base_url, client=client)
        return {"cors_domain": result}

    async def _run_domain_api(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        await self.emit_progress("domain_api_check")
        with http_request_category("api_checks"):
            result = await run_api_checks(base_url, client=client)
        return {"api_checks": result}

    def _get_domain_bundle(self, domain_results: dict[str, Any]) -> FindingsBundle:
        """Retourne le bundle domaine, calculé une seule fois par run."""
        if self._domain_bundle_cache is None:
            domain_only = {k: v for k, v in domain_results.items() if k != "cors_domain"}
            self._domain_bundle_cache = build_findings_bundle(domain_only, scan_type=self._scan_type)
        return self._domain_bundle_cache

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

        if response.status_code >= 500:
            err_msg = f"HTTP {response.status_code} (service unavailable)"
            logger.warning("multi_scan: page returned 5xx url=%s status=%s", url, response.status_code)
            await self.emit_progress("page_scan_error", url=url)
            return self._build_error_page_result(url, err_msg, domain_results)

        tls_result = domain_results.get("tls")
        is_https = getattr(tls_result, "https_enabled", True)
        page_check_results = await run_page_checks(
            response,
            url,
            client,
            assets_cache=self._assets_cache,
            is_https=is_https,
            domain_cors_result=domain_results.get("cors_domain"),
            scan_type=self._scan_type,
        )

        merged: dict[str, Any] = {k: v for k, v in domain_results.items() if k != "cors_domain"}
        merged.update(page_check_results)
        bundle: FindingsBundle = build_findings_bundle(merged, scan_type=self._scan_type)

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
        """Construit un résultat de page en erreur en réutilisant le bundle domaine mis en cache."""
        bundle = self._get_domain_bundle(domain_results)
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
    *,
    scan_type: str = "frontend",
) -> MultiScanResult:
    """Public passive multi-scan entrypoint."""
    orchestrator = PassiveMultiScanOrchestrator(on_progress=on_progress, scan_type=scan_type)
    return await orchestrator.run(urls)


async def validate_multi_scan_urls(urls: list[str]) -> list[str]:
    """Validate/normalize URLs and enforce single registered-domain + SSRF check."""
    return await validate_multi_scan_urls_common(urls)
