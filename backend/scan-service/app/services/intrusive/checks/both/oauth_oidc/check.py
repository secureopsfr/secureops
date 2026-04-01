"""Check : OAuth/OIDC Misuse (Phase C — P3).

Spec : docs/verifications/intrusive/oauth-oidc-misuse.md
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
from app.services.intrusive.lib.redirect_module import probe_redirect_uri

logger = logging.getLogger(__name__)

_CATEGORY = "oauth_oidc"
_OAUTH_ENDPOINTS = ["/oauth/authorize", "/auth/authorize", "/connect/authorize", "/oauth2/authorize", "/.well-known/openid-configuration"]
_STATE_RE = re.compile(r"state=([^&\s]+)", re.IGNORECASE)
_PKCE_RE = re.compile(r"code_challenge", re.IGNORECASE)


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les mauvaises configurations OAuth/OIDC."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"
    target_host = base.netloc.split(":")[0]

    for oauth_path in _OAUTH_ENDPOINTS[:3]:
        oauth_url = base_url + oauth_path
        try:
            r = await client.get(oauth_url)
            if r.status_code == 404:
                continue

            if r.status_code in (200, 302):
                # Tester redirect_uri avec domaine externe
                external = await probe_redirect_uri(client, oauth_url, target_host)
                if external:
                    findings.append(
                        make_finding(
                            slug="intrusive-oauth-open-redirect-uri",
                            category=_CATEGORY,
                            title="OAuth : redirect_uri non validé — redirection externe acceptée",
                            severity="high",
                            evidence=f"GET {oauth_url} redirect_uri externe → {external}",
                        )
                    )
                    return findings

                # Vérifier absence de state parameter dans les réponses 302
                location = r.location()
                if r.status_code == 302 and location and not _STATE_RE.search(location):
                    findings.append(
                        make_finding(
                            slug="intrusive-oauth-missing-state",
                            category=_CATEGORY,
                            title="OAuth : paramètre state absent (CSRF possible)",
                            severity="medium",
                            evidence=f"GET {oauth_url} → 302 Location sans state: {location[:120]}",
                        )
                    )

                break
        except Exception:
            logger.debug("oauth_oidc probe failed for %s", oauth_url, exc_info=True)

    return findings
