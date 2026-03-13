"""Generic orchestration primitives for multi-URL scan pipelines."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, TypeVar

OnProgress = Callable[..., Awaitable[None]] | None
PageResultT = TypeVar("PageResultT")
ResultT = TypeVar("ResultT")
ClientT = TypeVar("ClientT")


@dataclass(frozen=True)
class MultiScanExecutionSettings:
    """Execution settings shared by multi-scan pipelines."""

    concurrent_pages: int
    page_timeout: float


class SupportsErrorField(Protocol):
    """Protocol for page results exposing an optional error field."""

    error: str | None


class BaseMultiScanOrchestrator:
    """Template-method orchestrator reused by scan modes (passive/intrusive/...)."""

    def __init__(self, *, on_progress: OnProgress = None) -> None:
        """Initialize shared orchestration state and optional progress callback."""
        self.on_progress = on_progress

    async def emit_progress(self, step: str, message: str = "", **extra: Any) -> None:
        """Emit progress events when a callback is configured."""
        if self.on_progress:
            await self.on_progress(step, message, **extra)

    async def run(self, urls: list[str]) -> ResultT:
        """Run the generic multi-URL orchestration flow."""
        start = time.monotonic()
        base_url = self.resolve_base_url(urls)
        settings = self.get_execution_settings()

        async with self.get_client_context() as client:
            try:
                domain_results = await self.run_domain_phase(base_url, client)
                page_results = await self.run_pages_phase(
                    urls=urls,
                    client=client,
                    domain_results=domain_results,
                    settings=settings,
                )
            finally:
                await self.after_client_run(client=client, base_url=base_url, urls=urls)

        duration = time.monotonic() - start
        timestamp = datetime.now(timezone.utc).isoformat()
        score_global = self.compute_global_score(page_results)
        await self.emit_progress("multi_scan_done", score=score_global)
        return self.build_final_result(
            base_url=base_url,
            urls=urls,
            page_results=page_results,
            score_global=score_global,
            timestamp=timestamp,
            duration=duration,
        )

    async def run_pages_phase(
        self,
        *,
        urls: list[str],
        client: ClientT,
        domain_results: dict[str, Any],
        settings: MultiScanExecutionSettings,
    ) -> list[PageResultT]:
        """Run page scans with bounded concurrency."""
        semaphore = asyncio.Semaphore(settings.concurrent_pages)
        tasks = [
            self._run_page_with_semaphore(
                url=url,
                client=client,
                domain_results=domain_results,
                semaphore=semaphore,
                page_timeout=settings.page_timeout,
                page_index=i,
                total_pages=len(urls),
            )
            for i, url in enumerate(urls)
        ]
        return list(await asyncio.gather(*tasks))

    async def _run_page_with_semaphore(
        self,
        *,
        url: str,
        client: ClientT,
        domain_results: dict[str, Any],
        semaphore: asyncio.Semaphore,
        page_timeout: float,
        page_index: int,
        total_pages: int,
    ) -> PageResultT:
        async with semaphore:
            return await self.run_single_page(
                url=url,
                client=client,
                domain_results=domain_results,
                page_timeout=page_timeout,
                page_index=page_index,
                total_pages=total_pages,
            )

    def compute_global_score(self, page_results: list[SupportsErrorField]) -> int:
        """Default global score: weighted average, 0.5 weight for errored pages."""
        if not page_results:
            return 0
        weights = [0.5 if p.error else 1.0 for p in page_results]
        scores = [0 if p.error else int(getattr(p, "score", 0)) for p in page_results]
        total_weight = sum(weights)
        if total_weight == 0:
            return 0
        return int(sum(s * w for s, w in zip(scores, weights)) / total_weight)

    # Hooks implemented by concrete scan modes.
    def resolve_base_url(self, urls: list[str]) -> str:
        """Return the normalized base URL used by domain-level checks."""
        raise NotImplementedError

    def get_execution_settings(self) -> MultiScanExecutionSettings:
        """Provide runtime settings (timeouts/concurrency) for this pipeline."""
        raise NotImplementedError

    def get_client_context(self) -> AsyncIterator[ClientT]:
        """Return an async context manager yielding the HTTP client."""
        raise NotImplementedError

    async def run_domain_phase(self, base_url: str, client: ClientT) -> dict[str, Any]:
        """Execute domain-wide checks and return reusable intermediate results."""
        raise NotImplementedError

    async def run_single_page(
        self,
        *,
        url: str,
        client: ClientT,
        domain_results: dict[str, Any],
        page_timeout: float,
        page_index: int,
        total_pages: int,
    ) -> PageResultT:
        """Execute one page scan and return its page-level result object."""
        raise NotImplementedError

    def build_final_result(
        self,
        *,
        base_url: str,
        urls: list[str],
        page_results: list[PageResultT],
        score_global: int,
        timestamp: str,
        duration: float,
    ) -> ResultT:
        """Build and return the final aggregate multi-scan result."""
        raise NotImplementedError

    async def after_client_run(self, *, client: ClientT, base_url: str, urls: list[str]) -> None:
        """Optional hook executed after scan run, before leaving client context."""
        return None
