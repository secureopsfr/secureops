"""Check : IDOR / BOLA / BFLA simple (Phase A — P0).

Spec : docs/verifications/intrusive/autorisation-idor-bola-bfla.md
Domaine : per-page
Note Phase A : test sans cross-account (Phase B pour IDOR complet avec 2 sessions).
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse, urlunparse

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_ADMIN_ROUTES

logger = logging.getLogger(__name__)

_CATEGORY = "idor"

# Patterns d'IDs dans les URLs (UUID + entiers)
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_INT_ID_RE = re.compile(r"/(\d{1,10})(?:/|$|\?)")


def _increment_id_in_url(url: str, delta: int = 1) -> str | None:
    """Remplace un ID entier séquentiel dans le path par id+delta."""
    parsed = urlparse(url)
    match = _INT_ID_RE.search(parsed.path)
    if not match:
        return None
    original_id = int(match.group(1))
    new_id = original_id + delta
    if new_id <= 0:
        new_id = original_id - delta
    if new_id <= 0:
        return None
    end_id = match.end(1)
    new_path = parsed.path[: match.start(1)] + str(new_id) + parsed.path[end_id:]
    return urlunparse(parsed._replace(path=new_path))


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les accès non autorisés par modification d'IDs et routes admin."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # ─── IDOR : incrémentation d'ID entier dans le path ──────────────────────
    for delta in (1, -1):
        modified_url = _increment_id_in_url(url, delta)
        if not modified_url:
            continue
        try:
            baseline = await client.get(url)
            probe = await client.get(modified_url)
            if probe.success and probe.status_code == 200 and baseline.success and baseline.status_code == 200 and len(probe.body) > 50:
                findings.append(
                    make_finding(
                        slug="intrusive-idor-sequential-id",
                        category=_CATEGORY,
                        title="IDOR : accès à une ressource avec ID modifié",
                        severity="high",
                        evidence=f"GET {modified_url} → {probe.status_code} (ID {'+' if delta > 0 else ''}{delta})",
                    )
                )
                break
        except Exception:
            logger.debug("idor probe failed for %s", modified_url, exc_info=True)

    # ─── Routes admin non protégées ──────────────────────────────────────────
    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"
    for admin_path in COMMON_ADMIN_ROUTES[:5]:  # Budget limité
        admin_url = base_url + admin_path
        try:
            # Probe sans credentials pour tester l'accès anonyme
            anon_client = IntrusiveHTTPClient(
                credentials=None,  # Pas de credentials intentionnellement
                timeout=cfg.probe_timeout,
                jitter_min_ms=50,
                jitter_max_ms=100,
            )
            probe = await anon_client.get(admin_url)
            if probe.success and probe.status_code in (200, 201) and len(probe.body) > 100:
                findings.append(
                    make_finding(
                        slug="intrusive-idor-admin-route-exposed",
                        category=_CATEGORY,
                        title="Route admin accessible sans authentification",
                        severity="critical",
                        evidence=f"GET {admin_url} → {probe.status_code} ({len(probe.body)} octets)",
                    )
                )
        except Exception:
            logger.debug("idor admin probe failed for %s", admin_url, exc_info=True)

    return findings
