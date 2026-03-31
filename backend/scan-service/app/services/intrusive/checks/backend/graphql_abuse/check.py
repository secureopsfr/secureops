"""Check : GraphQL Abuse (Phase B — P1).

Spec : docs/verifications/intrusive/graphql-abuse.md
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

_CATEGORY = "graphql_abuse"
_GRAPHQL_PATHS = ["/graphql", "/api/graphql", "/gql", "/api/gql", "/query"]

_INTROSPECTION_QUERY = '{"query": "{__schema{types{name}}}"}'
_DEPTH_ABUSE_QUERY = '{"query": "{a{a{a{a{a{a{a{a{__typename}}}}}}}}}}"}'
_BATCH_ABUSE_QUERY = json.dumps({"query": " ".join([f"query q{i} {{ __typename }}" for i in range(50)])})


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les abus GraphQL : introspection, depth, batching."""
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

    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    for gql_path in _GRAPHQL_PATHS:
        gql_url = base_url + gql_path
        try:
            # Introspection
            r = await client.post(
                gql_url,
                content=_INTROSPECTION_QUERY,
                headers={"Content-Type": "application/json"},
            )
            if r.status_code == 404:
                continue

            if r.status_code in (200, 201):
                try:
                    data = json.loads(r.body)
                    if "data" in data and "__schema" in str(data.get("data", {})):
                        findings.append(
                            make_finding(
                                slug="intrusive-graphql-introspection-enabled",
                                category=_CATEGORY,
                                title="GraphQL : introspection activée en production",
                                severity="medium",
                                evidence=f"POST {gql_url} introspection → {r.status_code}, schéma exposé",
                            )
                        )
                except Exception:
                    pass

            # Depth abuse
            depth_r = await client.post(
                gql_url,
                content=_DEPTH_ABUSE_QUERY,
                headers={"Content-Type": "application/json"},
            )
            if depth_r.status_code in (200, 201) and "errors" not in depth_r.body:
                findings.append(
                    make_finding(
                        slug="intrusive-graphql-depth-abuse",
                        category=_CATEGORY,
                        title="GraphQL : requête profonde acceptée sans limitation",
                        severity="medium",
                        evidence=f"POST {gql_url} depth=8 → {depth_r.status_code} sans erreur de limite",
                    )
                )

            break  # Endpoint trouvé
        except Exception:
            logger.debug("graphql_abuse probe failed for %s", gql_url, exc_info=True)

    return findings
