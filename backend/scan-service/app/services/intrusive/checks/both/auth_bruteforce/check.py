"""Check : Auth bruteforce / lockout / énumération (Phase B — P0).

Spec : docs/verifications/intrusive/auth-bruteforce-lockout-enumeration.md
Domaine : domain-phase
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_LOGIN_ENDPOINTS

logger = logging.getLogger(__name__)

_CATEGORY = "auth_bruteforce"
_FAKE_CREDENTIALS = [
    ("wronguser1@test.invalid", "wrongpass1!"),
    ("wronguser2@test.invalid", "wrongpass2!"),
    ("wronguser3@test.invalid", "wrongpass3!"),
    ("wronguser4@test.invalid", "wrongpass4!"),
    ("wronguser5@test.invalid", "wrongpass5!"),
]


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte l'absence de protection bruteforce sur les endpoints d'authentification."""
    from urllib.parse import urlparse

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=None,  # Test anonyme intentionnel
        timeout=cfg.probe_timeout,
        jitter_min_ms=200,  # Délai plus long pour respecter les serveurs
        jitter_max_ms=500,
    )
    findings: list[Finding] = []

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for login_path in COMMON_LOGIN_ENDPOINTS[:3]:
        login_url = base_url + login_path
        locked_out = False
        attempts = 0

        for user, pwd in _FAKE_CREDENTIALS:
            if locked_out:
                break
            payload = {"username": user, "password": pwd, "email": user}
            try:
                r = await client.post(login_url, json=payload, headers={"Content-Type": "application/json"})
                attempts += 1
                if r.status_code == 429 or r.status_code == 423:
                    locked_out = True
                    break
                if r.status_code == 404:
                    break  # Endpoint inexistant
            except Exception:
                break

        if attempts >= 5 and not locked_out:
            findings.append(
                make_finding(
                    slug="intrusive-auth-no-lockout",
                    category=_CATEGORY,
                    title="Absence de protection bruteforce sur l'authentification",
                    severity="high",
                    evidence=f"{attempts} tentatives sur {login_url} sans lockout ni rate limiting (429/423)",
                )
            )

    return findings
