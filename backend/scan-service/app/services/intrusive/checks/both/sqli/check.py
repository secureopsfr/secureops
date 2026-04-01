"""Check : SQL Injection error-based + time-based léger (Phase A — P0).

Spec : docs/verifications/intrusive/injection-basique-erreurs.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_sql_error, detect_time_based
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "sql_injection"
_MAX_PARAMS = 5
_TIME_PAYLOADS = [
    "1' AND SLEEP(1)--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(1)))a)--",
    "1; WAITFOR DELAY '0:0:1'--",
    "1) AND SLEEP(1)--",
]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les injections SQL par error-based et time-based."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []
    params = extract_query_params(url)[:_MAX_PARAMS]

    for param in params:
        # ─── Error-based ─────────────────────────────────────────────────────
        for payload in get_payloads(PayloadCategory.SQL, budget=cfg.max_requests_per_param):
            probe_url = inject_query_param(url, param.name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                detection = detect_sql_error(result.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-sqli-error-based",
                            category=_CATEGORY,
                            title="Injection SQL détectée (error-based)",
                            severity="critical",
                            evidence=(f"Param '{param.name}' → payload: {payload.raw!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings  # Un finding critical suffit
            except Exception:
                logger.debug("sqli error-based probe failed param=%s", param.name, exc_info=True)

        # ─── Time-based (un seul paramètre par URL pour limiter la charge) ───
        if not findings and params:
            first_param = params[0]
            for tp in _TIME_PAYLOADS[:1]:  # Un seul payload time-based
                probe_url = inject_query_param(url, first_param.name, tp)

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
                            slug="intrusive-sqli-time-based",
                            category=_CATEGORY,
                            title="Injection SQL suspectée (time-based)",
                            severity="critical",
                            evidence=(f"Param '{first_param.name}' → payload: {tp!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings

    return findings
