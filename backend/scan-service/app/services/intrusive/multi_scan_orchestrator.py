"""Orchestration multi-URL du scan intrusif.

Implémente la séparation domain-phase / per-page décrite dans le roadmap §0.6.
scan_type et credentials sont propagés à chaque check.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config_loader import get_multi_scan_settings
from app.models.finding import Finding
from app.models.multi_scan import MultiScanResult, PageScanResult
from app.schemas.async_job import ScanCredentials
from app.services.intrusive._fake_security_checks import INTRUSIVE_STEPS
from app.services.intrusive.scan_stream import _should_skip_step
from app.services.mode_category_summaries import build_intrusive_category_summaries, count_total_tests
from app.services.pipelines.multi_scan_base import BaseMultiScanOrchestrator, MultiScanExecutionSettings, OnProgress
from app.services.scan_preflight_common import validate_multi_scan_urls_common
from app.services.scoring import compute_intrusive_score
from app.utils.http_fetch import get_with_client_or_error, log_http_metrics, scan_client
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)

# Checks exécutés une fois par domaine (domain-phase)
_DOMAIN_PHASE_STEPS: frozenset[str] = frozenset(
    {
        "cors_actif",
        "methodes_http",
        "graphql_abuse",
        "api_schema_abuse",
        "mass_assignment",
        "ssrf",
        "xxe",
        "grpc_abuse",
        "object_storage",
        "service_mesh",
        "auth_bruteforce",
        "dos_p0",
    }
)


class IntrusiveMultiScanOrchestrator(BaseMultiScanOrchestrator):
    """Orchestrateur multi-URL intrusif avec domain-phase / per-page split."""

    def __init__(
        self,
        *,
        on_progress: OnProgress = None,
        scan_type: str = "frontend",
        credentials: ScanCredentials | None = None,
    ) -> None:
        """Initialise l'orchestrateur avec le type de scan et les credentials cible."""
        super().__init__(on_progress=on_progress)
        self._scan_type = scan_type
        self._credentials = credentials

    def resolve_base_url(self, urls: list[str]) -> str:
        """Retourne l'URL de base de scan à partir de la première URL normalisée."""
        normalized_first = validate_and_normalize_url(urls[0])
        return get_scan_base_url(normalized_first)

    def get_execution_settings(self) -> MultiScanExecutionSettings:
        """Charge concurrence et timeout depuis la configuration multi-scan."""
        settings = get_multi_scan_settings()
        return MultiScanExecutionSettings(
            concurrent_pages=settings.concurrent_pages,
            page_timeout=settings.page_timeout,
        )

    def get_client_context(self):
        """Retourne le context manager httpx partagé pour le préflight."""
        return scan_client()

    async def after_client_run(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str,
        urls: list[str],
    ) -> None:
        """Journalise les métriques HTTP après exécution du client partagé."""
        log_http_metrics(client, "intrusive-multi-scan", base_url=base_url, urls=len(urls))

    async def run_domain_phase(
        self,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        """Exécute les checks domain-level (1× par domaine)."""
        domain_findings: list[Finding] = []
        await self.emit_progress("intrusive_domain_phase_started", url=base_url)

        for step_name, step_fn in INTRUSIVE_STEPS:
            if step_name not in _DOMAIN_PHASE_STEPS:
                continue
            if _should_skip_step(step_name, self._scan_type):
                continue
            await self.emit_progress(f"{step_name}_check", url=base_url)
            try:
                findings = await _run_step(step_fn, base_url, self._scan_type, self._credentials)
                domain_findings.extend(findings)
                await self.emit_progress(f"{step_name}_done", url=base_url, anomaly_count=len(findings))
            except Exception:
                logger.exception("Domain check %s failed for %s", step_name, base_url)

        await self.emit_progress("intrusive_domain_phase_done", url=base_url)
        return {"domain_findings": domain_findings}

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
        """Exécute les checks per-page pour une URL."""
        del page_timeout
        await self.emit_progress(
            "page_scan_started",
            url=url,
            page_index=page_index + 1,
            total_pages=total_pages,
        )

        fetch_result = await get_with_client_or_error(client, url, follow_redirects=True)
        if not fetch_result.success:
            await self.emit_progress("page_scan_error", url=url)
            return PageScanResult(url=url, score=0, findings=[], error="Page inaccessible for intrusive checks")

        findings: list[Finding] = list(domain_results.get("domain_findings", []))

        for step_name, step_fn in INTRUSIVE_STEPS:
            # Per-page = tout ce qui n'est pas domain-phase
            if step_name in _DOMAIN_PHASE_STEPS:
                continue
            if _should_skip_step(step_name, self._scan_type):
                continue
            await self.emit_progress(f"{step_name}_check", url=url)
            try:
                page_findings = await _run_step(step_fn, url, self._scan_type, self._credentials)
                findings.extend(page_findings)
                await self.emit_progress(f"{step_name}_done", url=url, anomaly_count=len(page_findings))
            except Exception:
                logger.exception("Per-page check %s failed for %s", step_name, url)

        await self.emit_progress("page_scan_done", url=url)
        summaries = build_intrusive_category_summaries(findings, scan_type=self._scan_type)
        return PageScanResult(
            url=url,
            score=compute_intrusive_score(findings),
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
        """Construit le résultat agrégé multi-pages pour la réponse API."""
        return MultiScanResult(
            base_url=base_url,
            urls=urls,
            score_global=score_global,
            page_results=page_results,
            timestamp=timestamp,
            duration=duration,
        )


async def _run_step(
    step_fn: Any,
    url: str,
    scan_type: str,
    credentials: ScanCredentials | None,
) -> list[Finding]:
    """Appelle un check (nouvelle interface async ou legacy fake probe)."""
    import inspect

    sig = inspect.signature(step_fn)
    if "scan_type" in sig.parameters:
        result = step_fn(url, scan_type=scan_type, credentials=credentials)
        if asyncio.iscoroutine(result):
            result = await result
        return result if isinstance(result, list) else []
    else:
        # Legacy fake probes
        result = step_fn(url)
        return list(getattr(result, "findings", []))


async def run_multi_scan(
    urls: list[str],
    on_progress: OnProgress = None,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> MultiScanResult:
    """Lance le scan multi-URL intrusif."""
    orchestrator = IntrusiveMultiScanOrchestrator(
        on_progress=on_progress,
        scan_type=scan_type,
        credentials=credentials,
    )
    return await orchestrator.run(urls)


async def validate_multi_scan_urls(urls: list[str]) -> list[str]:
    """Valide les URLs pour le scan multi-URL intrusif."""
    return await validate_multi_scan_urls_common(urls)
