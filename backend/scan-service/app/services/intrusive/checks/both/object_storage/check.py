"""Check : Object Storage Exposure actif (Phase C — P3).

Spec : docs/verifications/intrusive/object-storage-exposure-actif.md
Domaine : domain-phase
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

_CATEGORY = "object_storage"

_S3_BUCKET_RE = re.compile(r"(?:https?://)?([a-z0-9][a-z0-9\-]{1,62}\.s3(?:[.\-][a-z0-9\-]+)?\.amazonaws\.com)", re.IGNORECASE)
_GCS_BUCKET_RE = re.compile(r"(?:https?://)?storage\.googleapis\.com/([a-z0-9][a-z0-9\-_]{1,62})", re.IGNORECASE)
_AZURE_BLOB_RE = re.compile(r"(?:https?://)?([a-z0-9]{3,24})\.blob\.core\.windows\.net", re.IGNORECASE)


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les buckets cloud accessibles publiquement."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Récupérer la page pour trouver les références de buckets
    try:
        page = await client.get(url)
        if not page.success:
            return []
    except Exception:
        return []

    buckets: list[tuple[str, str]] = []  # (provider, bucket_url)

    for m in _S3_BUCKET_RE.finditer(page.body):
        bucket_host = m.group(1)
        buckets.append(("S3", f"https://{bucket_host}"))

    for m in _GCS_BUCKET_RE.finditer(page.body):
        bucket_name = m.group(1)
        buckets.append(("GCS", f"https://storage.googleapis.com/{bucket_name}"))

    for m in _AZURE_BLOB_RE.finditer(page.body):
        account = m.group(1)
        buckets.append(("Azure Blob", f"https://{account}.blob.core.windows.net"))

    # Tester le listing public
    probe_client = IntrusiveHTTPClient(credentials=None, timeout=cfg.probe_timeout)
    for provider, bucket_url in buckets[:3]:
        # Probe de listing
        list_urls = {
            "S3": f"{bucket_url}/?list-type=2",
            "GCS": f"{bucket_url}?maxResults=1",
            "Azure Blob": f"{bucket_url}?comp=list",
        }
        list_url = list_urls.get(provider, bucket_url)
        try:
            r = await probe_client.get(list_url)
            if r.success and r.status_code == 200 and ("<Key>" in r.body or "<item>" in r.body or "blob" in r.body.lower()):
                findings.append(
                    make_finding(
                        slug="intrusive-object-storage-public-listing",
                        category=_CATEGORY,
                        title=f"{provider} : listing public du bucket activé",
                        severity="high",
                        evidence=f"GET {list_url} → {r.status_code}, listing accessible sans auth",
                    )
                )
        except Exception:
            logger.debug("object_storage probe failed for %s", bucket_url, exc_info=True)

    return findings
