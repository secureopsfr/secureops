"""Check : gRPC Abuse (Phase C — P3).

Spec : docs/verifications/intrusive/grpc-abuse.md
Domaine : domain-phase
scan_type : BACKEND ONLY
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "grpc_abuse"


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les services gRPC exposés sans authentification."""
    if scan_type == "frontend":
        return []

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=None,  # Test anonyme
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)

    # Détecter gRPC reflection service sur port commun ou via HTTP/2
    for port in [50051, 50052, 9090]:
        grpc_url = f"https://{base.netloc.split(':')[0]}:{port}"
        try:
            r = await client.post(
                grpc_url + "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
                headers={"Content-Type": "application/grpc", "grpc-encoding": "identity"},
                content=b"\x00\x00\x00\x00\x02\x0a\x00",  # Minimal grpc frame
            )
            # gRPC retourne content-type: application/grpc
            ct = r.headers.get("content-type") or ""
            if "grpc" in ct.lower() and r.status_code in (200, 400):
                findings.append(
                    make_finding(
                        slug="intrusive-grpc-reflection-exposed",
                        category=_CATEGORY,
                        title="gRPC Reflection Service exposé sans authentification",
                        severity="medium",
                        evidence=f"POST {grpc_url}/grpc.reflection → {r.status_code}, Content-Type: {ct}",
                    )
                )
                return findings
        except Exception:
            pass  # Port non ouvert ou timeout = normal

    return findings
