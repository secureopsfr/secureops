"""Check : CORS actif (Phase A — P0).

Spec : docs/verifications/intrusive/cors-actif.md
Domaine : domain-phase
scan_type : backend → priorité plus élevée (APIs, données sensibles)
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "cors_actif"
_EVIL_ORIGIN = "https://evil.test"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les mauvaises configurations CORS par probe actif."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    try:
        result = await client.get(url, headers={"Origin": _EVIL_ORIGIN})
        if not result.success:
            return []

        acao = result.headers.get("access-control-allow-origin") or result.headers.get("Access-Control-Allow-Origin") or ""
        acac = result.headers.get("access-control-allow-credentials") or result.headers.get("Access-Control-Allow-Credentials") or ""

        is_reflected = acao.strip() == _EVIL_ORIGIN
        is_wildcard = acao.strip() == "*"
        has_credentials = acac.lower().strip() == "true"

        if is_reflected and has_credentials:
            # Critique : reflexion + credentials → vol de session possible
            severity = "critical"
            findings.append(
                make_finding(
                    slug="intrusive-cors-reflection-with-credentials",
                    category=_CATEGORY,
                    title="CORS : réflexion d'origine + credentials autorisés",
                    severity=severity,
                    evidence=(f"GET {url} Origin: {_EVIL_ORIGIN} → " f"ACAO: {acao}, ACAC: {acac}"),
                )
            )
        elif is_reflected:
            # Haute : réflexion sans credentials
            severity = "high" if scan_type == "backend" else "medium"
            findings.append(
                make_finding(
                    slug="intrusive-cors-reflection-no-credentials",
                    category=_CATEGORY,
                    title="CORS : réflexion d'origine arbitraire",
                    severity=severity,
                    evidence=f"GET {url} Origin: {_EVIL_ORIGIN} → ACAO: {acao}",
                )
            )
        elif is_wildcard:
            findings.append(
                make_finding(
                    slug="intrusive-cors-wildcard",
                    category=_CATEGORY,
                    title="CORS : wildcard Access-Control-Allow-Origin",
                    severity="medium",
                    evidence=f"GET {url} → ACAO: *",
                )
            )

        # Vérification Vary: Origin (bonne pratique)
        vary = result.headers.get("vary") or result.headers.get("Vary") or ""
        if (is_reflected or is_wildcard) and "origin" not in vary.lower():
            logger.debug("CORS: Vary: Origin absent for %s", url)

    except Exception:
        logger.debug("cors_actif probe failed for %s", url, exc_info=True)

    return findings
