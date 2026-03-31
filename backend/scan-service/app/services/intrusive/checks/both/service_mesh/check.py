"""Check : Service Mesh / Internal API Exposure (Phase C — P3).

Spec : docs/verifications/intrusive/service-mesh-internal-api-exposure.md
Domaine : domain-phase
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_INTERNAL_ENDPOINTS

logger = logging.getLogger(__name__)

_CATEGORY = "service_mesh"

# Indicateurs de contenu sensible dans les réponses
_SENSITIVE_INDICATORS = [
    "password",
    "secret",
    "api_key",
    "token",
    "credentials",
    "database_url",
    "db_url",
    "spring.datasource",
    "heap dump",
    "thread dump",
    "gc log",
    "java.lang.",
    "java.util.",
]


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les endpoints internes accidentellement exposés."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=None,  # Test anonyme pour vérifier l'exposition sans auth
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for endpoint in COMMON_INTERNAL_ENDPOINTS[:8]:  # Budget limité
        target = base_url + endpoint
        try:
            r = await client.get(target)
            if r.status_code not in (200, 206):
                continue
            if len(r.body) < 50:
                continue

            # Vérifier le contenu sensible
            body_lower = r.body.lower()
            found_indicators = [ind for ind in _SENSITIVE_INDICATORS if ind in body_lower]

            if found_indicators or endpoint in ("/actuator/env", "/actuator/heapdump", "/env"):
                severity = "critical" if found_indicators else "high"
                extra_ev = f", indicateurs: {found_indicators[:3]}" if found_indicators else ""
                findings.append(
                    make_finding(
                        slug="intrusive-internal-endpoint-exposed",
                        category=_CATEGORY,
                        title="Endpoint interne exposé sans authentification",
                        severity=severity,
                        evidence=f"GET {target} → {r.status_code} ({len(r.body)} octets){extra_ev}",
                    )
                )
        except Exception:
            logger.debug("service_mesh probe failed for %s", target, exc_info=True)

    return findings
