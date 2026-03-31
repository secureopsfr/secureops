"""Check : Upload Abuse (Phase B — P1).

Spec : docs/verifications/intrusive/upload-abuse.md
Domaine : per-page
scan_type : frontend (via <input type=file>) | backend (via patterns URL)
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_UPLOAD_ENDPOINTS, has_file_input

logger = logging.getLogger(__name__)

_CATEGORY = "upload_abuse"

# Fichiers de test avec content-type spoofé
_TEST_FILES = [
    {
        "filename": "test.php.jpg",
        "content": b"<?php echo 'test'; ?>",
        "content_type": "image/jpeg",
        "description": "PHP via double extension + MIME spoof",
    },
    {
        "filename": "test.jpg",
        "content": b"GIF89a<?php echo 'test'; ?>",
        "content_type": "image/jpeg",
        "description": "PHP caché dans GIF header",
    },
    {
        "filename": "../../../test.txt",
        "content": b"path traversal test",
        "content_type": "text/plain",
        "description": "Path traversal dans nom de fichier",
    },
]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités sur les endpoints d'upload."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Détecter les endpoints d'upload
    upload_endpoints: list[str] = []
    from urllib.parse import urlparse

    base = urlparse(url)
    base_url = f"{base.scheme}://{base.netloc}"

    if scan_type == "frontend":
        # Détecter via <input type="file"> dans la page
        try:
            page = await client.get(url)
            if page.success and has_file_input(page.body):
                upload_endpoints.append(url)
        except Exception:
            pass

    # Patterns URL communs
    for ep in COMMON_UPLOAD_ENDPOINTS:
        upload_endpoints.append(base_url + ep)

    for upload_url in upload_endpoints[:3]:
        for test_file in _TEST_FILES[:2]:  # Budget limité
            try:
                # Upload multipart simulé (sans vraie exécution côté serveur)
                file_content = test_file["content"]
                # Construction multipart basique
                boundary = "----SecureOpsBoundary"
                part_head = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="file"; filename="{test_file["filename"]}"\r\n'
                    f'Content-Type: {test_file["content_type"]}\r\n\r\n'
                ).encode()
                body = part_head + file_content + f"\r\n--{boundary}--\r\n".encode()

                result = await client.post(
                    upload_url,
                    content=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )

                if result.status_code in (200, 201) and result.body:
                    # Chercher un chemin de fichier dans la réponse
                    import re

                    file_path_re = re.compile(r'(?:url|path|location|file)["\s:=]+(["\']?)(/[^\s"\']+)', re.IGNORECASE)
                    m = file_path_re.search(result.body)
                    if m:
                        file_path = m.group(2)
                        # Tenter d'accéder au fichier uploadé
                        file_url = base_url + file_path
                        access = await client.get(file_url)
                        if access.success and access.status_code == 200:
                            findings.append(
                                make_finding(
                                    slug="intrusive-upload-file-accessible",
                                    category=_CATEGORY,
                                    title="Fichier uploadé accessible directement",
                                    severity="critical",
                                    evidence=(f"Upload {test_file['filename']} sur {upload_url} " f"→ accessible via {file_url}"),
                                )
                            )
                            return findings
            except Exception:
                logger.debug("upload_abuse probe failed for %s", upload_url, exc_info=True)

    return findings
