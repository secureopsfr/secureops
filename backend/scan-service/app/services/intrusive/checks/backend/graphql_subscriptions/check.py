"""Check : GraphQL Subscriptions Abuse (Phase C — P3).

Spec : docs/verifications/intrusive/graphql-subscriptions-abuse.md
Domaine : per-page
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

_CATEGORY = "graphql_subscriptions"
_SUBSCRIPTION_QUERY = '{"query": "subscription { __typename }"}'


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les abus sur les souscriptions GraphQL."""
    if scan_type == "frontend":
        return []

    cfg = get_intrusive_scan_settings()
    anon_client = IntrusiveHTTPClient(
        credentials=None,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for gql_path in ["/graphql", "/api/graphql", "/gql"]:
        gql_url = base_url + gql_path
        try:
            r = await anon_client.post(
                gql_url,
                content=_SUBSCRIPTION_QUERY,
                headers={"Content-Type": "application/json"},
            )
            if r.status_code == 404:
                continue
            if r.status_code in (200, 201):
                try:
                    data = json.loads(r.body)
                    if "errors" not in data:
                        findings.append(
                            make_finding(
                                slug="intrusive-graphql-subscription-no-auth",
                                category=_CATEGORY,
                                title="GraphQL : souscription acceptée sans authentification",
                                severity="high",
                                evidence=f"POST {gql_url} subscription anonyme → {r.status_code}",
                            )
                        )
                        return findings
                except Exception:
                    pass
        except Exception:
            logger.debug("graphql_subscriptions probe failed for %s", gql_url, exc_info=True)

    return findings
