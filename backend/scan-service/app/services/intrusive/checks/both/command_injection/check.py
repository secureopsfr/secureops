"""Check : Command Injection basique (Phase A — P0).

Spec : docs/verifications/intrusive/command-injection-basique.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_shell_output, detect_time_based
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_CMD_PARAMS, extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "command_injection"
_MAX_PARAMS = 3
_TIME_PAYLOADS = [";sleep 1", "|sleep 1", "$(sleep 1)"]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les injections de commandes système."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    candidate_names: set[str] = set(COMMON_CMD_PARAMS)
    for p in extract_query_params(url):
        candidate_names.add(p.name)

    payloads = get_payloads(PayloadCategory.SHELL, budget=cfg.max_requests_per_param)

    for param_name in list(candidate_names)[:_MAX_PARAMS]:
        # Error-based / output detection
        for payload in payloads:
            probe_url = inject_query_param(url, param_name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                detection = detect_shell_output(result.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-command-injection",
                            category=_CATEGORY,
                            title="Injection de commande système détectée",
                            severity="critical",
                            evidence=(f"Param '{param_name}' → payload: {payload.raw!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings
            except Exception:
                logger.debug("cmd injection probe failed param=%s", param_name, exc_info=True)

        # Time-based confirmation (un seul param pour limiter la charge)
        if not findings and param_name == list(candidate_names)[0]:
            for tp in _TIME_PAYLOADS[:1]:
                probe_url = inject_query_param(url, param_name, tp)

                async def _probe(url: str = probe_url) -> float:
                    r = await client.get(url)
                    return r.elapsed_ms

                detection = await detect_time_based(
                    _probe,
                    threshold_ms=cfg.time_based_threshold_ms,
                    confirmations=cfg.time_based_confirmations,
                )
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-command-injection",
                            category=_CATEGORY,
                            title="Injection de commande suspectée (time-based)",
                            severity="critical",
                            evidence=f"Param '{param_name}' → payload: {tp!r} → {detection.evidence}",
                        )
                    )
                    return findings

    return findings
