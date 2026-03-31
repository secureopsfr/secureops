"""Check : Session fixation / invalidation / JWT (Phase B — P0).

Spec : docs/verifications/intrusive/session-fixation-invalidation-token-lifecycle.md
Domaine : per-page
Requiert : credentials.cookie ou credentials.bearer_token pour test post-login.
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

_CATEGORY = "session_fixation"
_SET_COOKIE_RE = re.compile(r"([^=;]+)=([^;]*)", re.IGNORECASE)
_SESSION_COOKIE_NAMES = {"session", "sessionid", "sid", "phpsessid", "jsessionid", "aspsessionid", "laravel_session", "connect.sid"}


def _extract_session_id(set_cookie: str) -> str | None:
    """Extrait l'ID de session depuis un header Set-Cookie."""
    for m in _SET_COOKIE_RE.finditer(set_cookie):
        name = m.group(1).strip().lower()
        if name in _SESSION_COOKIE_NAMES:
            return m.group(2).strip()
    return None


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Vérifie la gestion du cycle de vie des sessions."""
    if not credentials:
        return []  # Nécessite une session active

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # ─── Session invalidation après logout ───────────────────────────────────
    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for logout_path in ["/logout", "/api/logout", "/auth/logout", "/signout"]:
        logout_url = base_url + logout_path
        try:
            logout = await client.post(logout_url, content="")
            if logout.status_code in (200, 302, 204):
                # Tester que les credentials sont rejetés après logout
                retry = await client.get(url)
                if retry.status_code in (200,) and len(retry.body) > 100:
                    findings.append(
                        make_finding(
                            slug="intrusive-session-not-invalidated",
                            category=_CATEGORY,
                            title="Session non invalidée après logout",
                            severity="high",
                            evidence=(f"POST {logout_url} → {logout.status_code} puis " f"GET {url} avec ancienne session → {retry.status_code}"),
                        )
                    )
                break
        except Exception:
            continue

    # ─── JWT : vérification des claims basiques ───────────────────────────────
    if credentials and credentials.bearer_token:
        token = credentials.bearer_token
        try:
            import base64

            parts = token.split(".")
            if len(parts) == 3:
                # Décoder le payload JWT (sans vérification de signature)
                payload_b64 = parts[1] + "=="
                payload_json = base64.b64decode(payload_b64).decode("utf-8", errors="replace")
                import json

                payload = json.loads(payload_json)
                # Vérifier absence d'exp
                if "exp" not in payload:
                    findings.append(
                        make_finding(
                            slug="intrusive-jwt-no-expiration",
                            category=_CATEGORY,
                            title="JWT sans expiration (claim exp absent)",
                            severity="medium",
                            evidence=f"Token JWT décodé sans claim 'exp'. Payload: {payload_json[:200]}",
                        )
                    )
        except Exception:
            pass

    return findings
