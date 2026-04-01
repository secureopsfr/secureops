"""Check : HTTP Request Smuggling / Desync (Phase C — P2).

Spec : docs/verifications/intrusive/request-smuggling-desync.md
Domaine : per-page
Sécurité : maximum 2 probes CL/TE par URL, réseau isolé recommandé.
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "request_smuggling"

# Probe CL/TE : Content-Length et Transfer-Encoding contradictoires
_CLTE_PROBE = "POST / HTTP/1.1\r\n" "Host: {host}\r\n" "Content-Length: 6\r\n" "Transfer-Encoding: chunked\r\n" "\r\n" "0\r\n" "\r\n" "G"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités HTTP request smuggling."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Probe 1 : Transfer-Encoding + Content-Length contradictoires
    try:
        result = await client.post(
            url,
            content="0\r\n\r\n",
            headers={
                "Content-Length": "6",
                "Transfer-Encoding": "chunked",
            },
        )
        # Indicateurs de désynchronisation : réponse 400 avec corps révélateur
        if result.status_code == 400 and "smuggl" in result.body.lower():
            findings.append(
                make_finding(
                    slug="intrusive-request-smuggling",
                    category=_CATEGORY,
                    title="Request smuggling — désynchronisation CL/TE potentielle",
                    severity="high",
                    evidence=f"POST {url} CL/TE contradictoires → {result.status_code}: {result.body[:100]}",
                )
            )
    except Exception:
        logger.debug("request_smuggling probe 1 failed for %s", url, exc_info=True)

    # Probe 2 : TE.TE obfusqué
    if not findings:
        try:
            result = await client.post(
                url,
                content="0\r\n\r\n",
                headers={
                    "Transfer-Encoding": "chunked",
                    "Transfer-encoding": "identity",  # Casse différente
                },
            )
            if result.status_code == 400 and len(result.body) > 10:
                findings.append(
                    make_finding(
                        slug="intrusive-request-smuggling",
                        category=_CATEGORY,
                        title="Request smuggling — TE.TE obfusqué potentiel",
                        severity="high",
                        evidence=f"POST {url} TE obfusqué → {result.status_code}",
                    )
                )
        except Exception:
            logger.debug("request_smuggling probe 2 failed for %s", url, exc_info=True)

    return findings
