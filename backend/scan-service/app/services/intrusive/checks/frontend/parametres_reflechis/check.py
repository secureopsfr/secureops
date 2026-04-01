"""Check : Paramètres réfléchis / XSS réfléchi (Phase A — P0).

Spec : docs/verifications/intrusive/parametres-reflechis.md
Domaine : per-page
scan_type : FRONTEND ONLY — skippé si scan_type == "backend"
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_reflection
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import detect_output_context, extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import make_xss_marker

logger = logging.getLogger(__name__)

_CATEGORY = "parametres_reflechis"
_MAX_PARAMS = 10


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les paramètres réfléchis non encodés (indicateur XSS)."""
    # FRONTEND ONLY — cette fonction ne devrait pas être appelée pour backend
    # (le skip logic est dans scan_stream.py) mais on garde la garde-fou ici
    if scan_type == "backend":
        return []

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
        marker = make_xss_marker()
        probe_url = inject_query_param(url, param.name, marker.raw)
        try:
            result = await client.get(probe_url)
            if not result.success:
                continue
            if detect_reflection(result.body, marker.raw):
                context = detect_output_context(result.body, marker.raw)
                severity = "high" if context in ("script", "attr") else "medium"
                slug = f"intrusive-reflected-param-in-{context}" if context != "none" else "intrusive-reflected-param"
                findings.append(
                    make_finding(
                        slug=slug,
                        category=_CATEGORY,
                        title="Paramètre réfléchi non encodé (XSS potentiel)",
                        severity=severity,
                        evidence=(f"Param '{param.name}' reflété dans contexte '{context}'. " f"Marker: {marker.raw} | URL: {probe_url}"),
                    )
                )
        except Exception:
            logger.debug("reflected param probe failed param=%s url=%s", param.name, url, exc_info=True)

    return findings
