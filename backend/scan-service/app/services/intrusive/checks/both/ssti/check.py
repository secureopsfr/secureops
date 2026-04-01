"""Check : SSTI — Server Side Template Injection (Phase B — P1).

Spec : docs/verifications/intrusive/ssti.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_ssti_eval, detect_template_error
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import make_ssti_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "ssti"
_MAX_PARAMS = 5


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les injections de template côté serveur."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []
    params = extract_query_params(url)[:_MAX_PARAMS]
    payloads = make_ssti_payloads()

    for param in params:
        for payload in payloads[:2]:  # Budget : 2 payloads par paramètre
            probe_url = inject_query_param(url, param.name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue

                # Détection de l'évaluation (7*7=49)
                if detect_ssti_eval(result.body):
                    findings.append(
                        make_finding(
                            slug="intrusive-ssti",
                            category=_CATEGORY,
                            title="SSTI détectée — expression de template évaluée",
                            severity="critical",
                            evidence=(f"Param '{param.name}' → payload: {payload.raw!r} " f"→ résultat '49' dans la réponse"),
                        )
                    )
                    return findings

                # Erreur de template révélatrice
                template_error = detect_template_error(result.body)
                if template_error.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-ssti-error",
                            category=_CATEGORY,
                            title="SSTI suspectée — erreur de moteur de template révélée",
                            severity="high",
                            evidence=(f"Param '{param.name}' → payload: {payload.raw!r} " f"→ {template_error.evidence}"),
                        )
                    )
                    return findings
            except Exception:
                logger.debug("ssti probe failed param=%s", param.name, exc_info=True)

    return findings
