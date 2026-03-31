"""Check : NoSQL Injection basique (Phase A — P0).

Spec : docs/verifications/intrusive/nosqli.md
Domaine : per-page
"""

from __future__ import annotations

import json
import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_nosql_error
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import get_nosql_qs_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "nosql_injection"
_MAX_PARAMS = 5
# Payloads JSON pour injection dans body
_NOSQL_JSON_PAYLOADS: list[dict] = [
    {"$ne": None},
    {"$gt": ""},
    {"$regex": ".*"},
]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les injections NoSQL (MongoDB operators)."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []
    params = extract_query_params(url)[:_MAX_PARAMS]

    # ─── Query string : [$ne]=1 etc. ─────────────────────────────────────────
    for param in params:
        for payload in get_nosql_qs_payloads(budget=cfg.max_requests_per_param):
            # Injection via query string bracket notation
            probe_url = inject_query_param(url, f"{param.name}", payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                detection = detect_nosql_error(result.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-nosqli-operator-injection",
                            category=_CATEGORY,
                            title="Injection NoSQL détectée",
                            severity="critical",
                            evidence=(f"Param '{param.name}' → payload: {payload.raw!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings

                # Bypass d'auth (200 inattendu)
                baseline = await client.get(url)
                if baseline.success and result.status_code == 200 and baseline.status_code in (401, 403):
                    findings.append(
                        make_finding(
                            slug="intrusive-nosqli-auth-bypass",
                            category=_CATEGORY,
                            title="Injection NoSQL : bypass d'authentification potentiel",
                            severity="critical",
                            evidence=(
                                f"Param '{param.name}' → payload: {payload.raw!r} " f"→ {result.status_code} (baseline: {baseline.status_code})"
                            ),
                        )
                    )
                    return findings
            except Exception:
                logger.debug("nosqli probe failed param=%s", param.name, exc_info=True)

    # ─── Body JSON : injection dans body POST (backend) ──────────────────────
    if scan_type == "backend" and not findings:
        for param in params[:2]:
            for nosql_obj in _NOSQL_JSON_PAYLOADS:
                body_payload = json.dumps({param.name: nosql_obj})
                try:
                    result = await client.post(
                        url,
                        content=body_payload,
                        headers={"Content-Type": "application/json"},
                    )
                    if not result.success:
                        continue
                    detection = detect_nosql_error(result.body)
                    if detection.matched:
                        findings.append(
                            make_finding(
                                slug="intrusive-nosqli-operator-injection",
                                category=_CATEGORY,
                                title="Injection NoSQL détectée (body JSON)",
                                severity="critical",
                                evidence=(f"Body param '{param.name}' → {body_payload!r} " f"→ {detection.evidence}"),
                            )
                        )
                        return findings
                except Exception:
                    logger.debug("nosqli body probe failed param=%s", param.name, exc_info=True)

    return findings
