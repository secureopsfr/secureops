"""Check : CSRF enforcement (Phase A — P0).

Spec : docs/verifications/intrusive/csrf-enforcement.md
Domaine : per-page
scan_type :
  - frontend : complet (formulaires POST + replay + SameSite)
  - backend  : partiel (skip si Bearer/API key ; SameSite si cookies)
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

_CATEGORY = "csrf"

_FORM_ACTION_RE = re.compile(r'<form[^>]+method=["\']?post["\']?[^>]*action=["\']?([^"\'>\s]+)', re.IGNORECASE)
_FORM_METHOD_RE = re.compile(r'<form[^>]+method=["\']?post["\']?', re.IGNORECASE)
_CSRF_FIELD_RE = re.compile(r'<input[^>]+name=["\']?(csrf[_-]?token|_token|authenticity_token|__RequestVerificationToken)["\']?', re.IGNORECASE)
_SAMESITE_RE = re.compile(r"SameSite=(Lax|Strict|None)", re.IGNORECASE)


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les failles CSRF sur endpoints POST."""
    cfg = get_intrusive_scan_settings()

    # Backend : skip si Bearer token fourni (protection CSRF implicite)
    if scan_type == "backend" and credentials and credentials.bearer_token:
        return []

    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Récupérer la page
    try:
        page = await client.get(url)
        if not page.success:
            return []
    except Exception:
        return []

    if scan_type == "frontend":
        # Chercher des formulaires POST sans token CSRF
        has_post_form = bool(_FORM_METHOD_RE.search(page.body))
        has_csrf_field = bool(_CSRF_FIELD_RE.search(page.body))

        if has_post_form and not has_csrf_field:
            # Tenter un replay POST sans token sur l'URL courante
            try:
                replay = await client.post(url, content="test=1")
                if replay.success and replay.status_code in (200, 201):
                    findings.append(
                        make_finding(
                            slug="intrusive-csrf-token-not-enforced",
                            category=_CATEGORY,
                            title="CSRF : formulaire POST accepté sans token",
                            severity="high",
                            evidence=f"POST {url} sans token CSRF → {replay.status_code}",
                        )
                    )
            except Exception:
                pass

    # Vérification SameSite sur les cookies (frontend + backend si cookies)
    set_cookie = page.headers.get("set-cookie") or page.headers.get("Set-Cookie") or ""
    if set_cookie and not _SAMESITE_RE.search(set_cookie):
        severity = "medium" if scan_type == "frontend" else "low"
        findings.append(
            make_finding(
                slug="intrusive-csrf-samesite-absent",
                category=_CATEGORY,
                title="CSRF : attribut SameSite absent sur le cookie de session",
                severity=severity,
                evidence=f"Set-Cookie: {set_cookie[:120]}",
            )
        )

    return findings
