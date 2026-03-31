"""Check : SSRF applicative (Phase B — P1).

Spec : docs/verifications/intrusive/ssrf-applicative.md
Domaine : domain-phase
Sécurité : payloads safe uniquement, détection in-band exclusivement.
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "ssrf"
_SSRF_PARAM_NAMES = {"url", "webhook", "callback", "fetch", "proxy", "endpoint", "dest", "destination", "redirect", "uri", "href"}
_SSRF_INDICATORS = [
    "169.254.169.254",
    "EC2 IMDS",
    "metadata",
    "/latest/meta-data",
    "ami-id",
    "instance-id",
    "127.0.0.1",
    "localhost",
    "Connection refused",
    "ECONNREFUSED",
]


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités SSRF in-band."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Collecter les paramètres candidats
    candidate_params = [p for p in extract_query_params(url) if p.name.lower() in _SSRF_PARAM_NAMES]
    # Ajouter les paramètres communs si aucun trouvé
    if not candidate_params:
        for name in list(_SSRF_PARAM_NAMES)[:3]:
            from app.services.intrusive.lib.param_extractor import ExtractedParam, ParamContext

            candidate_params.append(ExtractedParam(name=name, value="", context=ParamContext.QUERY_STRING, original_url=url))

    payloads = get_payloads(PayloadCategory.SSRF, budget=cfg.max_requests_per_param)

    for param in candidate_params[:3]:
        for payload in payloads[:2]:
            probe_url = inject_query_param(url, param.name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                # Vérifier indicateurs SSRF in-band
                for indicator in _SSRF_INDICATORS:
                    if indicator.lower() in result.body.lower():
                        findings.append(
                            make_finding(
                                slug="intrusive-ssrf-inband",
                                category=_CATEGORY,
                                title="SSRF détectée (in-band)",
                                severity="critical",
                                evidence=(f"Param '{param.name}' → payload: {payload.raw!r} " f"→ indicateur '{indicator}' dans la réponse"),
                            )
                        )
                        return findings
            except Exception:
                logger.debug("ssrf probe failed param=%s", param.name, exc_info=True)

    return findings
