"""Check : DoS contrôlé / Rate Limit detection (Phase A — P0).

Spec : docs/verifications/intrusive/dos-single-source.md
Domaine : domain-phase
Sécurité : burst sans sleep artificiel (20 req max), durée cap 3s, arrêt immédiat au premier 429.

Logique de détection :
  - On envoie jusqu'à 20 requêtes GET aussi vite que la réponse le permet.
  - Si l'on complète 15+ requêtes sans jamais recevoir de 429, on conclut
    à une absence de rate limiting significatif.
  - Un rate limiter correctement configuré (ex : 10 req/s) doit répondre
    429 bien avant d'atteindre ce seuil.
"""

from __future__ import annotations

import logging
import time

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "dos_rate_limit"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte l'absence de rate limiting par un burst rapide et contrôlé."""
    cfg = get_intrusive_scan_settings()
    # Pas de jitter — on veut mesurer la réaction à un vrai burst
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=0,
        jitter_max_ms=0,
    )

    burst_count = cfg.dos_burst_count
    max_duration = cfg.dos_burst_duration_s
    min_for_finding = cfg.dos_min_requests_for_finding
    start = time.monotonic()
    got_rate_limited = False
    responses_sent = 0

    try:
        for _ in range(burst_count):
            if time.monotonic() - start > max_duration:
                break
            result = await client.get(url)
            responses_sent += 1
            if result.status_code == 429:
                got_rate_limited = True
                break
    except Exception:
        logger.debug("dos_p0 probe failed for %s", url, exc_info=True)
        return []

    elapsed = time.monotonic() - start

    if not got_rate_limited and responses_sent >= min_for_finding:
        rate = responses_sent / elapsed if elapsed > 0 else 0
        return [
            make_finding(
                slug="intrusive-no-rate-limiting",
                category=_CATEGORY,
                title="Absence de rate limiting détectée",
                severity="medium",
                evidence=(f"{responses_sent} requêtes envoyées en {elapsed:.1f}s " f"({rate:.0f} req/s) sans aucun 429. URL: {url}"),
            )
        ]

    return []
