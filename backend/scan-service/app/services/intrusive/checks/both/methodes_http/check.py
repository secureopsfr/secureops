"""Check : Méthodes HTTP actives (Phase A — P0).

Spec : docs/verifications/intrusive/methodes-http-actives.md
Domaine : domain-phase
scan_type : frontend (severity=low) | backend (severity=info) pour méthodes dangereuses
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "methodes_http"
_DANGEROUS_METHODS = {"PUT", "DELETE", "PATCH", "CONNECT"}


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les méthodes HTTP potentiellement dangereuses exposées."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # 1. OPTIONS — récupérer les méthodes autorisées
    allowed_methods: set[str] = set()
    try:
        opts = await client.options(url)
        if opts.success:
            allow_header = opts.headers.get("allow") or opts.headers.get("Allow") or ""
            acam_header = opts.headers.get("access-control-allow-methods") or opts.headers.get("Access-Control-Allow-Methods") or ""
            raw = allow_header + "," + acam_header
            allowed_methods = {m.strip().upper() for m in raw.split(",") if m.strip()}
    except Exception:
        pass

    # 2. TRACE — XST (Cross-Site Tracing)
    try:
        trace = await client.trace(url)
        if trace.success and trace.status_code == 200 and len(trace.body) > 0:
            findings.append(
                make_finding(
                    slug="intrusive-trace-enabled",
                    category=_CATEGORY,
                    title="Méthode TRACE activée (XST)",
                    severity="medium",
                    evidence=f"TRACE {url} → {trace.status_code}, corps reflété ({len(trace.body)} octets)",
                )
            )
    except Exception:
        pass

    # 3. Méthodes dangereuses dans Allow
    dangerous_found = allowed_methods & _DANGEROUS_METHODS
    if dangerous_found:
        # Sévérité différenciée selon scan_type
        severity = "low" if scan_type == "frontend" else "info"
        findings.append(
            make_finding(
                slug="intrusive-dangerous-methods-allowed",
                category=_CATEGORY,
                title="Méthodes HTTP dangereuses autorisées",
                severity=severity,
                evidence=f"OPTIONS {url} → Allow: {', '.join(sorted(dangerous_found))}",
            )
        )

    return findings
