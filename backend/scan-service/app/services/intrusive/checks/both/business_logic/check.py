"""Check : Business Logic Abuse (Phase C — P2).

Spec : docs/verifications/intrusive/business-logic-abuse.md
Domaine : per-page
"""

from __future__ import annotations

import json
import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "business_logic"

_NEGATIVE_AMOUNT_PAYLOADS = [
    {"amount": -100},
    {"quantity": -1},
    {"price": -0.01},
    {"total": -999},
]

_INVALID_STATE_PAYLOADS = [
    {"status": "completed"},
    {"state": "approved"},
    {"verified": True},
    {"step": 999},
]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les abus de logique métier (montants négatifs, états invalides)."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Montants négatifs
    for payload in _NEGATIVE_AMOUNT_PAYLOADS[:2]:
        body = json.dumps(payload)
        try:
            result = await client.post(
                url,
                content=body,
                headers={"Content-Type": "application/json"},
            )
            if result.status_code in (200, 201):
                findings.append(
                    make_finding(
                        slug="intrusive-business-logic-negative-amount",
                        category=_CATEGORY,
                        title="Business Logic : montant/quantité négatif accepté",
                        severity="high",
                        evidence=f"POST {url} {body} → {result.status_code}",
                    )
                )
                break
        except Exception:
            logger.debug("business_logic probe failed for %s", url, exc_info=True)

    # États invalides
    if not findings:
        from urllib.parse import urlparse

        base = urlparse(url)
        base_url = f"{base.scheme}://{base.netloc}"

        for endpoint in ["/api/orders", "/api/checkout", "/api/payment"]:
            target = base_url + endpoint
            for payload in _INVALID_STATE_PAYLOADS[:1]:
                body = json.dumps(payload)
                try:
                    result = await client.patch(
                        target,
                        content=body,
                        headers={"Content-Type": "application/json"},
                    )
                    if result.status_code in (200, 201, 204):
                        findings.append(
                            make_finding(
                                slug="intrusive-business-logic-state-manipulation",
                                category=_CATEGORY,
                                title="Business Logic : manipulation d'état acceptée",
                                severity="medium",
                                evidence=f"PATCH {target} {body} → {result.status_code}",
                            )
                        )
                        return findings
                except Exception:
                    pass

    return findings
