"""Check : WebSocket Authorization (Phase C — P3).

Spec : docs/verifications/intrusive/websocket-authz.md
Domaine : per-page
"""

from __future__ import annotations

import logging
import re

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "websocket_authz"
_WS_INDICATOR_RE = re.compile(r"(?:ws://|wss://|WebSocket|socket\.io|sockjs)", re.IGNORECASE)


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les problèmes d'autorisation WebSocket."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Détecter des endpoints WebSocket dans la page
    try:
        page = await client.get(url)
        if not page.success:
            return []
        ws_found = _WS_INDICATOR_RE.search(page.body)
    except Exception:
        return []

    if not ws_found:
        return []

    # Tenter un upgrade WebSocket anonyme
    from urllib.parse import urlparse

    base = urlparse(url)
    ws_paths = ["/ws", "/socket", "/socket.io", "/api/ws", "/events"]
    base_url = f"{base.scheme}://{base.netloc}"

    for ws_path in ws_paths[:3]:
        ws_url = base_url + ws_path
        try:
            # Handshake WebSocket via HTTP upgrade
            anon_client = IntrusiveHTTPClient(credentials=None, timeout=cfg.probe_timeout)
            upgrade_r = await anon_client.get(
                ws_url,
                headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                },
            )
            if upgrade_r.status_code == 101:
                findings.append(
                    make_finding(
                        slug="intrusive-websocket-no-auth",
                        category=_CATEGORY,
                        title="WebSocket : upgrade accepté sans authentification",
                        severity="high",
                        evidence=f"GET {ws_url} Upgrade: websocket → {upgrade_r.status_code} (101 Switching Protocols)",
                    )
                )
                return findings
        except Exception:
            logger.debug("websocket_authz probe failed for %s", ws_url, exc_info=True)

    return findings
