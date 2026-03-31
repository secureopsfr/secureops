"""Check : Path Traversal (Phase A — P0).

Spec : docs/verifications/intrusive/path-traversal-leger.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_path_traversal
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_FILE_PARAMS, extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "path_traversal"
_MAX_PARAMS = 3


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités de path traversal."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Paramètres ciblés : fichier-related + ceux détectés dans l'URL
    candidate_names: set[str] = set(COMMON_FILE_PARAMS)
    for p in extract_query_params(url):
        candidate_names.add(p.name)

    payloads = get_payloads(PayloadCategory.PATH, budget=cfg.max_requests_per_param)

    for param_name in list(candidate_names)[:_MAX_PARAMS]:
        for payload in payloads:
            probe_url = inject_query_param(url, param_name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                detection = detect_path_traversal(result.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-path-traversal",
                            category=_CATEGORY,
                            title="Path traversal détecté",
                            severity="high",
                            evidence=(f"Param '{param_name}' → payload: {payload.raw!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings
            except Exception:
                logger.debug("path_traversal probe failed param=%s", param_name, exc_info=True)

    return findings
