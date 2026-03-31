"""Check : XXE (Phase B — P1).

Spec : docs/verifications/intrusive/xxe.md
Domaine : domain-phase
Détection : in-band uniquement (OOB déféré à 1.2.0).
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_path_traversal, detect_xxe
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "xxe"
_XML_ENDPOINTS_INDICATORS = [".xml", "xml", "soap", "wsdl", "rss", "atom", "feed"]


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités XXE par probe in-band."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Détecter si l'endpoint est susceptible d'accepter du XML
    url_lower = url.lower()
    is_xml_candidate = any(ind in url_lower for ind in _XML_ENDPOINTS_INDICATORS)

    targets = [url]
    if not is_xml_candidate:
        # Ajouter des candidats communs
        from urllib.parse import urlparse

        base = urlparse(url)
        base_url = f"{base.scheme}://{base.netloc}"
        for path in ["/api/xml", "/feed.xml", "/sitemap.xml", "/rss.xml"]:
            targets.append(base_url + path)

    payloads = get_payloads(PayloadCategory.XML, budget=2)

    for target in targets[:2]:
        for payload in payloads:
            try:
                result = await client.post(
                    target,
                    content=payload.raw.encode(),
                    headers={"Content-Type": "application/xml"},
                )
                if not result.success:
                    continue

                # Détection in-band
                xxe_detection = detect_xxe(result.body)
                path_detection = detect_path_traversal(result.body)

                if xxe_detection.matched or path_detection.matched:
                    detection = xxe_detection if xxe_detection.matched else path_detection
                    findings.append(
                        make_finding(
                            slug="intrusive-xxe-inband",
                            category=_CATEGORY,
                            title="XXE détectée (in-band)",
                            severity="critical",
                            evidence=f"POST {target} XML payload → {detection.evidence}",
                        )
                    )
                    return findings
            except Exception:
                logger.debug("xxe probe failed for %s", target, exc_info=True)

    return findings
