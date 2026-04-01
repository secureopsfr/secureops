"""Check : Host Header Injection (Phase C — P2).

Spec : docs/verifications/intrusive/host-header-injection.md
Domaine : per-page
"""

from __future__ import annotations

import logging
import re

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "host_header"
_EVIL_HOST = "evil.test"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les injections via Host header."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    for header_name, header_value in [
        ("Host", _EVIL_HOST),
        ("X-Forwarded-Host", _EVIL_HOST),
        ("X-Host", _EVIL_HOST),
    ]:
        try:
            result = await client.get(url, headers={header_name: header_value})
            if not result.success:
                continue
            # Chercher evil.test dans la réponse (réflexion dans liens, cookies, etc.)
            if _EVIL_HOST in result.body:
                # Chercher spécifiquement dans les liens de reset ou les URLs
                link_re = re.compile(rf'href=["\']([^"\']*{re.escape(_EVIL_HOST)}[^"\']*)["\']', re.IGNORECASE)
                m = link_re.search(result.body)
                evidence_detail = f"reflété dans le body, lien: {m.group(1)}" if m else "reflété dans le body"
                findings.append(
                    make_finding(
                        slug="intrusive-host-header-injection",
                        category=_CATEGORY,
                        title="Host Header Injection — hôte contrôlé reflété",
                        severity="high",
                        evidence=f"{header_name}: {header_value} → {evidence_detail}",
                    )
                )
                return findings
        except Exception:
            logger.debug("host_header probe failed for %s", url, exc_info=True)

    return findings
