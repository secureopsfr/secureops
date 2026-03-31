"""Check : API Schema Validation Abuse (Phase B — P1).

Spec : docs/verifications/intrusive/api-schema-validation-abuse.md
Domaine : domain-phase
scan_type : BACKEND ONLY
"""

from __future__ import annotations

import json
import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "api_schema_abuse"


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les lacunes de validation du schéma API."""
    if scan_type == "frontend":
        return []

    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Type confusion : envoyer types inattendus
    type_confusion_payloads = [
        {"id": ["array", "instead", "of", "string"]},
        {"limit": "not_a_number"},
        {"page": {"nested": "object"}},
        {"__proto__": {"admin": True}},
    ]

    for payload in type_confusion_payloads[:2]:
        body = json.dumps(payload)
        try:
            result = await client.post(
                url,
                content=body,
                headers={"Content-Type": "application/json"},
            )
            if result.status_code in (200, 201):
                findings.append(
                    make_finding(
                        slug="intrusive-api-schema-no-validation",
                        category=_CATEGORY,
                        title="API : absence de validation du schéma (type confusion acceptée)",
                        severity="medium",
                        evidence=(f"POST {url} avec payload: {body!r} → {result.status_code} " f"(400/422 attendu)"),
                    )
                )
                break
        except Exception:
            logger.debug("api_schema_abuse probe failed for %s", url, exc_info=True)

    # Arrays excessifs : limit=99999
    try:
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params["limit"] = ["99999"]
        params["page"] = ["-1"]
        new_qs = urlencode({k: v[0] for k, v in params.items()})
        test_url = urlunparse(parsed._replace(query=new_qs))
        result = await client.get(test_url)
        if result.status_code in (200, 201):
            try:
                data = json.loads(result.body)
                if isinstance(data, list) and len(data) > 100:
                    findings.append(
                        make_finding(
                            slug="intrusive-api-schema-unlimited-list",
                            category=_CATEGORY,
                            title="API : liste illimitée acceptée (limit=99999)",
                            severity="low",
                            evidence=f"GET {test_url} → {result.status_code}, {len(data)} éléments retournés",
                        )
                    )
            except Exception:
                pass
    except Exception:
        pass

    return findings
