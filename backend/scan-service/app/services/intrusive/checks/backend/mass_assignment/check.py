"""Check : Mass Assignment (Phase B — P1).

Spec : docs/verifications/intrusive/mass-assignment.md
Domaine : domain-phase
scan_type : BACKEND ONLY
"""

from __future__ import annotations

import json
import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.payload_engine import get_mass_assignment_fields

logger = logging.getLogger(__name__)

_CATEGORY = "mass_assignment"
_REST_ENDPOINTS = ["/api/users", "/api/profile", "/api/account", "/api/me", "/api/user"]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités de mass assignment dans les APIs REST."""
    if scan_type == "frontend":
        return []

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

    sensitive_fields = get_mass_assignment_fields()

    # Tester PUT/PATCH sur l'URL courante et endpoints REST courants
    test_targets = [url] + [base_url + ep for ep in _REST_ENDPOINTS[:2]]

    for target in test_targets[:2]:
        # Construire un payload avec champs sensibles
        payload = dict(sensitive_fields[:5])
        body = json.dumps(payload)

        for method in ("PUT", "PATCH"):
            try:
                baseline = await client.get(target)
                if baseline.status_code == 404:
                    continue

                result = await client.request(
                    method,
                    target,
                    content=body,
                    headers={"Content-Type": "application/json"},
                )

                if result.status_code in (200, 201, 204):
                    # Vérifier si les champs sensibles sont reflétés dans la réponse
                    try:
                        resp_data = json.loads(result.body)
                        accepted_fields = [f for f, _ in sensitive_fields[:5] if str(f) in str(resp_data)]
                        if accepted_fields:
                            findings.append(
                                make_finding(
                                    slug="intrusive-mass-assignment",
                                    category=_CATEGORY,
                                    title="Mass assignment : champs sensibles acceptés sans whitelist",
                                    severity="high",
                                    evidence=(
                                        f"{method} {target} avec champs {accepted_fields} " f"→ {result.status_code}, champs reflétés dans la réponse"
                                    ),
                                )
                            )
                            return findings
                    except Exception:
                        pass
            except Exception:
                logger.debug("mass_assignment probe failed for %s", target, exc_info=True)

    return findings
