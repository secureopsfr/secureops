"""Detection of exposed sensitive files and endpoints (roadmap §3.4).

Tests a fixed list of paths (/.env, /.git/config, etc.) and detects exposure
when status 200 + content matches known signatures.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config_loader import get_exposed_files_max_body, get_exposed_files_settings
from app.utils.http_fetch import fetch_url, get_with_client
from app.utils.url_helpers import build_https_url, build_url_with_path

if TYPE_CHECKING:
    import httpx


@dataclass
class ExposedEndpoint:
    """An exposed sensitive endpoint.

    Attributes:
        path (str): Path tested (e.g. /.env).
        severity (str): critical, high, medium, low.
        message (str): Finding message.
    """

    path: str
    severity: str
    message: str


@dataclass
class ExposedFilesCheckResult:
    """Result of exposed files checks.

    Attributes:
        exposed (tuple[ExposedEndpoint, ...]): List of exposed endpoints.
        findings (tuple[str, ...]): Finding messages.
        fetch_ok (bool): True if at least one request succeeded.
    """

    exposed: tuple[ExposedEndpoint, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Serialize for SSE result event."""
        exposed_serialized = [{"path": e.path, "severity": e.severity, "message": e.message} for e in self.exposed]
        return {
            "exposed": exposed_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def _content_matches_env(body: bytes, _path: str) -> bool:
    """Check if body looks like .env (KEY=value, DATABASE_, SECRET_, etc.)."""
    text = body.decode("utf-8", errors="replace").lower()
    if not re.search(r"^[a-z0-9_]+=.*$", text[:200], re.MULTILINE | re.IGNORECASE):
        return False
    return any(kw in text for kw in ("database_url", "secret_key", "api_key", "password", "db_password"))


def _content_matches_git_config(body: bytes, _path: str) -> bool:
    """Check if body looks like .git/config."""
    text = body.decode("utf-8", errors="replace").lower()
    return "[core]" in text or "[remote" in text or "repositoryformatversion" in text


def _content_matches_zip(body: bytes, _path: str) -> bool:
    """Check if body is a ZIP file (starts with PK)."""
    return len(body) > 0 and body[:2] == b"PK"


def _content_matches_phpinfo(body: bytes, _path: str) -> bool:
    """Check if body contains phpinfo output."""
    text = body.decode("utf-8", errors="replace").lower()
    return "phpinfo" in text and ("php version" in text or "configuration" in text)


def _content_matches_admin(body: bytes, _path: str) -> bool:
    """Check if body looks like admin login page (form with username/password)."""
    text = body.decode("utf-8", errors="replace").lower()
    has_form = "form" in text and ("password" in text or "passwd" in text)
    has_login = "login" in text or "username" in text or "administrator" in text
    return has_form or (has_login and len(body) > 500)


def _content_matches_ds_store(body: bytes, _path: str) -> bool:
    """Check if body looks like .DS_Store (Bud1, DSDB)."""
    return b"Bud1" in body[:1024] or b"DSDB" in body[:1024]


_SIGNATURE_CHECKERS: dict[str, callable] = {
    "/.env": _content_matches_env,
    "/.git/config": _content_matches_git_config,
    "/backup.zip": _content_matches_zip,
    "/phpinfo.php": _content_matches_phpinfo,
    "/admin/": _content_matches_admin,
    "/.ds_store": _content_matches_ds_store,  # .DS_Store normalisé en minuscules
}


def _get_checker_for_path(path: str):
    """Return the signature checker for a path (normalized)."""
    path_normalized = path.rstrip("/") if path != "/" else path
    key = path_normalized.lower()
    if key in _SIGNATURE_CHECKERS:
        return _SIGNATURE_CHECKERS[key]
    if path_normalized == "/.git/config":
        return _content_matches_git_config
    return None


async def _check_single_path(
    base_url: str,
    config_path: str,
    severity: str,
    message: str,
    max_body: int,
    *,
    client: "httpx.AsyncClient | None" = None,
) -> tuple[ExposedEndpoint | None, bool]:
    """Test one path. Returns (ExposedEndpoint if exposed else None, got_response)."""
    full_url = build_url_with_path(base_url, config_path)
    if client is not None:
        response = await get_with_client(client, full_url, follow_redirects=False)
    else:
        response = await fetch_url(full_url, follow_redirects=False)
    if response is None:
        return None, False
    if response.status_code != 200:
        return None, True

    body = response.content[:max_body]
    if len(body) == 0:
        return None, True

    checker = _get_checker_for_path(config_path)
    if checker is None:
        return None, True

    if checker(body, config_path):
        return ExposedEndpoint(path=config_path, severity=severity, message=message), True
    return None, True


async def run_exposed_files_checks(
    base_url: str,
    *,
    client: "httpx.AsyncClient | None" = None,
) -> ExposedFilesCheckResult:
    """Test all configured sensitive paths for exposure.

    Performs GET requests in parallel. A path is considered exposed if status 200
    and content matches known signatures. Si client est fourni, réutilise la
    connexion TCP (keep-alive).

    Args:
        base_url: Base URL (e.g. https://example.com/).
        client: Client httpx optionnel (issu de scan_client()) pour réutilisation.

    Returns:
        ExposedFilesCheckResult: Exposed endpoints and findings.
    """
    https_base = build_https_url(base_url)
    configs = get_exposed_files_settings()
    max_body = get_exposed_files_max_body()

    tasks = [_check_single_path(https_base, c.path, c.severity, c.message, max_body, client=client) for c in configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    exposed: list[ExposedEndpoint] = []
    fetch_ok = False
    for r in results:
        if isinstance(r, Exception):
            continue
        endpoint, got_response = r
        if got_response:
            fetch_ok = True
        if endpoint is not None:
            exposed.append(endpoint)

    findings = tuple(e.message for e in exposed)

    return ExposedFilesCheckResult(
        exposed=tuple(exposed),
        findings=findings,
        fetch_ok=fetch_ok,
    )
