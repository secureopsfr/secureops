"""Logique générique pour les vérifications par chemin (fetch → 200 → body check).

Utilisé par exposed_files et directory_listing. Le body_checker_fn détermine
si le contenu correspond à une signature (fichier sensible, listing Apache/Nginx).
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.utils.http_fetch import fetch_url, get_with_client
from app.utils.url_helpers import build_url_with_path

if TYPE_CHECKING:
    import httpx


@dataclass
class PathFinding:
    """Finding pour un chemin testé (fichier exposé, répertoire avec listing).

    Attributes:
        path (str): Chemin testé (ex. /.env, /uploads/).
        severity (str): critical, high, medium, low.
        message (str): Message du finding.
    """

    path: str
    severity: str
    message: str


@dataclass
class PathCheckResult:
    """Résultat des vérifications par chemin (exposed_files, directory_listing).

    Attributes:
        exposed (tuple[PathFinding, ...]): Chemins avec finding.
        findings (tuple[str, ...]): Messages des findings.
        fetch_ok (bool): True si au moins une requête a réussi.
    """

    exposed: tuple[PathFinding, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        exposed_serialized = [{"path": e.path, "severity": e.severity, "message": e.message} for e in self.exposed]
        return {
            "exposed": exposed_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


async def _check_single_path(
    base_url: str,
    path: str,
    severity: str,
    message: str,
    max_body: int,
    body_checker_fn: Callable[[bytes, str], bool],
    *,
    client: "httpx.AsyncClient | None" = None,
) -> tuple[PathFinding | None, bool]:
    """Teste un chemin. Retourne (PathFinding si match, None sinon, got_response)."""
    full_url = build_url_with_path(base_url, path)
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

    if body_checker_fn(body, path):
        return PathFinding(path=path, severity=severity, message=message), True
    return None, True


async def run_path_checks(
    base_url: str,
    configs: tuple,
    body_checker_fn: Callable[[bytes, str], bool],
    max_body: int,
    *,
    client: "httpx.AsyncClient | None" = None,
) -> PathCheckResult:
    """Exécute les vérifications par chemin en parallèle.

    Pour chaque config (path, severity, message), effectue GET, vérifie status 200
    et applique body_checker_fn(body, path). Si True → finding.

    Args:
        base_url: URL de base (ex. https://example.com/).
        configs: Tuple de configs avec .path, .severity, .message.
        body_checker_fn: (body: bytes, path: str) -> bool.
        max_body: Limite de lecture du corps (octets).
        client: Client httpx optionnel pour réutilisation.

    Returns:
        PathCheckResult: Findings et fetch_ok.
    """
    tasks = [_check_single_path(base_url, c.path, c.severity, c.message, max_body, body_checker_fn, client=client) for c in configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    exposed: list[PathFinding] = []
    fetch_ok = False
    for r in results:
        if isinstance(r, Exception):
            continue
        finding, got_response = r
        if got_response:
            fetch_ok = True
        if finding is not None:
            exposed.append(finding)

    findings = tuple(e.message for e in exposed)

    return PathCheckResult(
        exposed=tuple(exposed),
        findings=findings,
        fetch_ok=fetch_ok,
    )
