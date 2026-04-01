"""Check : Race Conditions (Phase C — P2).

Spec : docs/verifications/intrusive/race-conditions.md
Domaine : per-page
Sécurité : max 3 requêtes simultanées sur endpoints sensibles.
"""

from __future__ import annotations

import asyncio
import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "race_conditions"
_SENSITIVE_ENDPOINTS = [
    "/api/transfer",
    "/api/payment",
    "/api/checkout",
    "/api/order",
    "/api/vote",
    "/api/like",
    "/api/subscribe",
    "/api/redeem",
]


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les race conditions par envoi simultané de 2–3 requêtes."""
    if not credentials:
        return []  # Nécessite une session pour des tests significatifs

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=0,  # Pas de jitter — on veut la simultanéité
        jitter_max_ms=0,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for endpoint in _SENSITIVE_ENDPOINTS[:3]:
        target = base_url + endpoint
        try:
            # Vérifier que l'endpoint existe
            probe = await client.get(target)
            if probe.status_code == 404:
                continue

            # Envoi simultané de 3 requêtes POST identiques
            tasks = [client.post(target, json={"amount": 1}) for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if hasattr(r, "status_code") and r.status_code in (200, 201))

            if success_count >= 2:
                findings.append(
                    make_finding(
                        slug="intrusive-race-condition",
                        category=_CATEGORY,
                        title="Race condition potentielle — endpoint sensible sans idempotence",
                        severity="high",
                        evidence=(f"3 requêtes simultanées sur {target} " f"→ {success_count} succès (200/201)"),
                    )
                )
                return findings
        except Exception:
            logger.debug("race_conditions probe failed for %s", target, exc_info=True)

    return findings
