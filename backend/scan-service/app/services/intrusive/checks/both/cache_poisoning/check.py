"""Check : Cache Poisoning / Web Cache Deception (Phase C — P2).

Spec : docs/verifications/intrusive/cache-poisoning-web-cache-deception.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "cache_poisoning"
_EVIL_HOST = "evil.test"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte le cache poisoning et le web cache deception."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # ─── Cache Poisoning via headers non normalisés ───────────────────────────
    try:
        # Envoi avec X-Forwarded-Host
        await client.get(url, headers={"X-Forwarded-Host": _EVIL_HOST})
        # Seconde requête sans le header pour voir si le cache a été pollué
        clean = await client.get(url)
        if clean.success and _EVIL_HOST in clean.body:
            findings.append(
                make_finding(
                    slug="intrusive-cache-poisoning",
                    category=_CATEGORY,
                    title="Cache poisoning via X-Forwarded-Host",
                    severity="high",
                    evidence=f"X-Forwarded-Host: {_EVIL_HOST} → {_EVIL_HOST} dans réponse cache ultérieure",
                )
            )
    except Exception:
        logger.debug("cache_poisoning probe failed for %s", url, exc_info=True)

    # ─── Web Cache Deception ──────────────────────────────────────────────────
    if not findings and scan_type == "frontend":
        from urllib.parse import urlparse

        base = urlparse(url)
        for sensitive_path in ["/profile", "/account", "/settings", "/dashboard"]:
            wcd_url = f"{base.scheme}://{base.netloc}{sensitive_path}/nonexistent.css"
            try:
                with_creds = await client.get(wcd_url)
                without_creds = IntrusiveHTTPClient(credentials=None, timeout=cfg.probe_timeout)
                anon = await without_creds.get(wcd_url)
                ok_creds = with_creds.success and with_creds.status_code == 200
                ok_anon = anon.success and anon.status_code == 200
                ok_size = len(anon.body) > 200 and len(anon.body) > len(with_creds.body) * 0.5
                if ok_creds and ok_anon and ok_size:
                    findings.append(
                        make_finding(
                            slug="intrusive-web-cache-deception",
                            category=_CATEGORY,
                            title="Web Cache Deception potentiel",
                            severity="high",
                            evidence=f"GET {wcd_url} accessible anonymement ({len(anon.body)} octets)",
                        )
                    )
                    break
            except Exception:
                continue

    return findings
