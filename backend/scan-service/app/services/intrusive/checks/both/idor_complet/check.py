"""Check : IDOR complet avec sessions croisées (Phase B — P0 suite).

Spec : docs/verifications/intrusive/autorisation-idor-bola-bfla.md
Complète idor/check.py Phase A avec escalade verticale via credentials.
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_ADMIN_ROUTES

logger = logging.getLogger(__name__)

_CATEGORY = "idor"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Test IDOR complet avec session authentifiée : escalade verticale."""
    if not credentials:
        return []  # Complément de idor Phase A, nécessite credentials

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    anon_client = IntrusiveHTTPClient(
        credentials=None,
        timeout=cfg.probe_timeout,
        jitter_min_ms=50,
        jitter_max_ms=100,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    # Escalade verticale : tenter routes admin avec session standard
    for admin_path in COMMON_ADMIN_ROUTES[:4]:
        admin_url = base_url + admin_path
        try:
            # D'abord vérifier que l'endpoint existe (anon → 401/403)
            anon_r = await anon_client.get(admin_url)
            if anon_r.status_code not in (401, 403):
                continue  # Pas une route protégée

            # Tenter avec session standard
            auth_r = await client.get(admin_url)
            if auth_r.success and auth_r.status_code in (200, 201) and len(auth_r.body) > 100:
                findings.append(
                    make_finding(
                        slug="intrusive-idor-privilege-escalation",
                        category=_CATEGORY,
                        title="IDOR : escalade de privilèges — route admin accessible avec session standard",
                        severity="critical",
                        evidence=(
                            f"GET {admin_url} → anon: {anon_r.status_code}, " f"avec session: {auth_r.status_code} ({len(auth_r.body)} octets)"
                        ),
                    )
                )
        except Exception:
            logger.debug("idor_complet probe failed for %s", admin_url, exc_info=True)

    return findings
