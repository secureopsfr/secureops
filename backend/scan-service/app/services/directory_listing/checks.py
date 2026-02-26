"""Détection du directory listing (roadmap §3.5).

Teste une liste de répertoires usuels (/uploads/, /assets/, /static/) et détecte
si le serveur renvoie une page de listing (signatures Apache/Nginx).
Réutilise get_with_client, fetch_url, build_https_url, build_url_with_path.
"""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config_loader import get_directory_listing_max_body, get_directory_listing_settings
from app.utils.http_fetch import fetch_url, get_with_client
from app.utils.url_helpers import build_https_url, build_url_with_path

if TYPE_CHECKING:
    import httpx


@dataclass
class DirectoryListingEntry:
    """Répertoire avec listing activé.

    Attributes:
        path (str): Chemin testé (ex. /uploads/).
        severity (str): critical, high, medium, low.
        message (str): Message du finding.
    """

    path: str
    severity: str
    message: str


@dataclass
class DirectoryListingCheckResult:
    """Résultat des vérifications directory listing.

    Attributes:
        exposed (tuple[DirectoryListingEntry, ...]): Répertoires avec listing activé.
        findings (tuple[str, ...]): Messages des findings.
        fetch_ok (bool): True si au moins une requête a réussi.
    """

    exposed: tuple[DirectoryListingEntry, ...]
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


def _is_listing_body(body: bytes) -> bool:
    """Détecte si le corps correspond à une page de listing Apache/Nginx.

    Signatures typiques : Index of, Parent Directory, [DIR], mod_autoindex (Apache),
    nginx, <a href=" (Nginx). Évite les faux positifs en exigeant plusieurs motifs.

    Args:
        body: Corps de la réponse HTTP (octets).

    Returns:
        bool: True si le contenu ressemble à une page de listing.
    """
    if len(body) == 0:
        return False
    text = body.decode("utf-8", errors="replace").lower()
    if "index of" not in text:
        return False
    # Au moins un motif supplémentaire pour réduire les faux positifs
    apache_signatures = ("parent directory", "[dir]", "mod_autoindex", "<title>index of")
    nginx_signatures = ("<a href=", "nginx")
    if any(s in text for s in apache_signatures):
        return True
    if any(s in text for s in nginx_signatures):
        return True
    return False


async def _check_single_directory(
    base_url: str,
    config_path: str,
    severity: str,
    message: str,
    max_body: int,
    *,
    client: "httpx.AsyncClient | None" = None,
) -> tuple[DirectoryListingEntry | None, bool]:
    """Teste un répertoire. Retourne (DirectoryListingEntry si listing, None sinon, got_response)."""
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

    if _is_listing_body(body):
        return DirectoryListingEntry(path=config_path, severity=severity, message=message), True
    return None, True


async def run_directory_listing_checks(
    base_url: str,
    *,
    client: "httpx.AsyncClient | None" = None,
) -> DirectoryListingCheckResult:
    """Teste tous les répertoires configurés pour le directory listing.

    Effectue des requêtes GET en parallèle. Un répertoire est considéré vulnérable
    si status 200 et contenu contient les signatures Apache/Nginx de listing.
    Si client est fourni, réutilise la connexion TCP (keep-alive).

    Args:
        base_url: URL de base (ex. https://example.com/).
        client: Client httpx optionnel (issu de scan_client()) pour réutilisation.

    Returns:
        DirectoryListingCheckResult: Répertoires exposés et findings.
    """
    https_base = build_https_url(base_url)
    configs = get_directory_listing_settings()
    max_body = get_directory_listing_max_body()

    tasks = [_check_single_directory(https_base, c.path, c.severity, c.message, max_body, client=client) for c in configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    exposed: list[DirectoryListingEntry] = []
    fetch_ok = False
    for r in results:
        if isinstance(r, Exception):
            continue
        entry, got_response = r
        if got_response:
            fetch_ok = True
        if entry is not None:
            exposed.append(entry)

    findings = tuple(e.message for e in exposed)

    return DirectoryListingCheckResult(
        exposed=tuple(exposed),
        findings=findings,
        fetch_ok=fetch_ok,
    )
