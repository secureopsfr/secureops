"""Pipeline SSE du scan intrusif.

Remplace progressivement les fake probes de _fake_security_checks.py
par les vrais checks de services/intrusive/checks/*.

scan_type propagation :
  - _INTRUSIVE_FRONTEND_ONLY_STEPS : skippés si scan_type == "backend"
  - _INTRUSIVE_BACKEND_ONLY_STEPS  : skippés si scan_type == "frontend"
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Callable

from app.config_loader import get_scan_timeouts
from app.errors.fetch_errors import build_sse_error_payload, build_timeout_global_error_payload
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive._fake_security_checks import INTRUSIVE_STEPS
from app.services.intrusive._scan_core import build_result_payload
from app.services.scan_preflight_common import emit_events, has_error_event, run_single_preflight
from app.services.scan_stream_common import emit_save_events, stream_with_standard_error_events
from app.utils.http_fetch import get_with_client_or_error, log_http_metrics, scan_client
from app.utils.sse import sse_message
from app.utils.url_helpers import get_scan_base_url

logger = logging.getLogger(__name__)

# Étapes réservées au frontend (HTML context requis)
_INTRUSIVE_FRONTEND_ONLY_STEPS: frozenset[str] = frozenset({"parametres_reflechis"})

# Étapes réservées au backend (APIs, protocoles non-HTML)
_INTRUSIVE_BACKEND_ONLY_STEPS: frozenset[str] = frozenset(
    {
        "mass_assignment",
        "graphql_abuse",
        "graphql_subscriptions",
        "api_schema_abuse",
        "grpc_abuse",
    }
)


def _timeout_error_message() -> str:
    return sse_message("error", build_timeout_global_error_payload())


def _should_skip_step(step_name: str, scan_type: str) -> bool:
    """Retourne True si le step doit être ignoré pour ce scan_type."""
    if scan_type == "backend" and step_name in _INTRUSIVE_FRONTEND_ONLY_STEPS:
        return True
    if scan_type == "frontend" and step_name in _INTRUSIVE_BACKEND_ONLY_STEPS:
        return True
    return False


async def _perform_intrusive_checks(
    normalized_url: str,
    over_global: Callable[[], bool],
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> tuple[list[Finding], list[str], bool]:
    """Fetch la cible et exécute les checks intrusifs en respectant scan_type."""
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
                if _should_skip_step(step_name, scan_type):
                    continue
                if over_global():
                    events.append(_timeout_error_message())
                    return findings, events, True

                events.append(sse_message("step", {"step": f"{step_name}_check", "message": ""}))
                try:
                    import inspect

                    sig = inspect.signature(step_fn)
                    if "scan_type" in sig.parameters:
                        result = await _call_check(step_fn, normalized_url, scan_type=scan_type, credentials=credentials)
                    else:
                        # Legacy fake probes : signature (url,) uniquement
                        import asyncio

                        r = step_fn(normalized_url)
                        if asyncio.iscoroutine(r):
                            r = await r
                        findings.extend(r.findings)
                        events.append(sse_message("step", {"step": f"{step_name}_done", "message": "", "anomaly_count": len(r.findings)}))
                        continue
                    findings.extend(result)
                except Exception:
                    logger.exception("Intrusive check %s failed for %s", step_name, normalized_url)
                    result = []

                events.append(sse_message("step", {"step": f"{step_name}_done", "message": "", "anomaly_count": len(result)}))
        finally:
            log_http_metrics(client, "intrusive-scan-stream", url=https_url)

    return findings, events, False


async def _call_check(
    step_fn: Callable,
    url: str,
    scan_type: str,
    credentials: ScanCredentials | None,
) -> list[Finding]:
    """Appelle un check avec la nouvelle interface async."""
    import asyncio

    result = step_fn(url, scan_type=scan_type, credentials=credentials)
    if asyncio.iscoroutine(result):
        result = await result
    if isinstance(result, list):
        return result
    # Compatibilité IntrusiveCheckResult (fake probes)
    return list(getattr(result, "findings", []))


async def _run_pipeline_steps(
    url: str,
    authorization: str | None = None,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> AsyncGenerator[str, None]:
    """Exécute le flux intrusif et émet les chunks SSE."""
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    normalized_url, preflight_events = await run_single_preflight(
        url=url,
        over_global=_over_global,
        timeout_error_message_factory=_timeout_error_message,
    )
    async for chunk in emit_events(preflight_events):
        yield chunk
    if has_error_event(preflight_events):
        return
    if normalized_url is None:
        return

    findings, check_events, should_stop = await _perform_intrusive_checks(normalized_url, _over_global, scan_type=scan_type, credentials=credentials)
    async for chunk in emit_events(check_events):
        yield chunk
    if should_stop:
        return

    payload = build_result_payload(normalized_url, findings, start, scan_type=scan_type)
    yield sse_message("result", payload)
    async for chunk in emit_save_events(
        payload=payload,
        authorization=authorization,
        logger=logger,
        mode_label="Intrusive",
    ):
        yield chunk


async def scan_stream_generator(
    url: str,
    authorization: str | None = None,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
    input_json: dict | None = None,
) -> AsyncGenerator[str, None]:
    """Générateur SSE du scan intrusif.

    Args:
        url: URL cible.
        authorization: JWT/API key SecureOps (pour la sauvegarde).
        scan_type: "frontend" ou "backend" — conditionne les checks exécutés.
        credentials: Credentials optionnels de l'application cible.
    """
    async for chunk in stream_with_standard_error_events(
        pipeline_factory=lambda: _run_pipeline_steps(
            url,
            authorization=authorization,
            scan_type=scan_type,
            credentials=credentials,
        ),
    ):
        yield chunk
