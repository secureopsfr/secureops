"""Détection du directory listing (roadmap §3.5).

Teste une liste de répertoires usuels (/uploads/, /assets/, /static/, /tmp/, /logs/, etc.)
et détecte si le serveur renvoie une page de listing (signatures Apache/Nginx ou listing partiel).
Gère aussi les 403 sur chemins sensibles (existence révélée).
"""

import asyncio
import re

from app.config_loader import get_directory_listing_max_body, get_directory_listing_settings
from app.services.path_checks import PathCheckResult, PathFinding
from app.utils.http_fetch import fetch_url, get_with_client
from app.utils.url_helpers import build_url_with_path

# Chemins sensibles : un 403 indique l'existence du répertoire (protection active).
_SENSITIVE_FOR_403 = ("/config/", "/backup/", "/logs/", "/tmp/", "/data/")

# Extensions de fichiers typiques dans un listing partiel.
_PARTIAL_LISTING_EXTENSIONS = (
    ".pdf",
    ".zip",
    ".csv",
    ".xlsx",
    ".xls",
    ".txt",
    ".log",
    ".sql",
    ".bak",
    ".env",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".conf",
    ".ini",
    ".config",
    ".tar",
    ".gz",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
)

# Seuil minimum de liens pour considérer un listing partiel (éviter faux positifs).
_PARTIAL_LISTING_MIN_LINKS = 3


def _is_listing_body(body: bytes, _path: str) -> bool:
    """Détecte si le corps correspond à une page de listing Apache/Nginx ou partiel.

    Signatures typiques : Index of, Parent Directory, [DIR], mod_autoindex (Apache),
    nginx, <a href=" (Nginx). Évite les faux positifs en exigeant plusieurs motifs.
    Détecte aussi les listings partiels : HTML avec plusieurs liens vers fichiers.

    Args:
        body: Corps de la réponse HTTP (octets).
        _path: Chemin testé (non utilisé, signature identique pour tous).

    Returns:
        bool: True si le contenu ressemble à une page de listing.
    """
    if len(body) == 0:
        return False
    text = body.decode("utf-8", errors="replace").lower()
    # Détection Apache/Nginx (signatures classiques)
    if "index of" in text:
        apache_signatures = ("parent directory", "[dir]", "mod_autoindex", "<title>index of")
        nginx_signatures = ("<a href=", "nginx")
        if any(s in text for s in apache_signatures):
            return True
        if any(s in text for s in nginx_signatures):
            return True
    # Détection listing partiel : HTML avec liens vers fichiers (sans signature Apache/Nginx)
    return _is_partial_listing_body(text)


def _is_partial_listing_body(text: str) -> bool:
    """Détecte un listing partiel : HTML avec plusieurs liens vers fichiers ou sous-dossiers.

    Args:
        text: Corps décodé en minuscules.

    Returns:
        bool: True si listing partiel détecté (≥ N liens vers fichiers/dossiers).
    """
    if "<a href=" not in text and "<a " not in text:
        return False
    # Recherche des liens <a href="...">
    pattern = re.compile(r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    matches = pattern.findall(text)
    count = 0
    for href in matches:
        href = href.strip().lower()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        # Dossier : chemin se terminant par /
        if href.endswith("/"):
            count += 1
            continue
        # Fichier : extension connue
        if any(href.endswith(ext) for ext in _PARTIAL_LISTING_EXTENSIONS):
            count += 1
            continue
        # Lien relatif simple (ex. "fichier.pdf" ou "sous-dossier/")
        if "/" not in href and "." in href:
            count += 1
    return count >= _PARTIAL_LISTING_MIN_LINKS


async def _check_single_directory_path(
    base_url: str,
    path: str,
    severity: str,
    message: str,
    max_body: int,
    *,
    client=None,
) -> tuple[PathFinding | None, PathFinding | None, bool]:
    """Teste un chemin. Retourne (finding si listing 200, finding si 403 sensible, got_response).

    Args:
        base_url: URL de base.
        path: Chemin à tester.
        severity: Sévérité du finding.
        message: Message du finding.
        max_body: Limite de lecture du corps.
        client: Client httpx optionnel.

    Returns:
        tuple: (PathFinding si 200+listing, PathFinding si 403 sensible, got_response).
    """
    full_url = build_url_with_path(base_url, path)
    if client is not None:
        response = await get_with_client(client, full_url, follow_redirects=False)
    else:
        response = await fetch_url(full_url, follow_redirects=False)
    if response is None:
        return None, None, False
    if response.status_code == 403:
        path_norm = (path.rstrip("/") + "/") if path else "/"
        if path_norm in _SENSITIVE_FOR_403:
            msg_403 = f"Répertoire sensible {path} retourne 403 : existence révélée."
            return None, PathFinding(path=path, severity="medium", message=msg_403), True
        return None, None, True
    if response.status_code != 200:
        return None, None, True
    body = response.content[:max_body]
    if len(body) == 0:
        return None, None, True
    if _is_listing_body(body, path):
        return PathFinding(path=path, severity=severity, message=message), None, True
    return None, None, True


async def run_directory_listing_checks(
    base_url: str,
    *,
    client=None,
) -> PathCheckResult:
    """Teste tous les répertoires configurés pour le directory listing.

    Effectue des requêtes GET en parallèle. Un répertoire est considéré vulnérable si :
    - status 200 et contenu contient les signatures Apache/Nginx ou un listing partiel ;
    - status 403 sur un chemin sensible (/config/, /backup/, /logs/, /tmp/, /data/).
    Si client est fourni, réutilise la connexion TCP (keep-alive).

    Args:
        base_url: URL de base HTTPS (ex. https://example.com/). L'appelant fournit déjà ctx.https_url.
        client: Client httpx optionnel (issu de scan_client()) pour réutilisation.

    Returns:
        PathCheckResult: Répertoires exposés, findings et exposed_403.
    """
    configs = get_directory_listing_settings()
    max_body = get_directory_listing_max_body()
    tasks = [_check_single_directory_path(base_url, c.path, c.severity, c.message, max_body, client=client) for c in configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    exposed: list[PathFinding] = []
    exposed_403: list[PathFinding] = []
    fetch_ok = False
    for r in results:
        if isinstance(r, Exception):
            continue
        finding_200, finding_403, got_response = r
        if got_response:
            fetch_ok = True
        if finding_200 is not None:
            exposed.append(finding_200)
        if finding_403 is not None:
            exposed_403.append(finding_403)

    findings = tuple(e.message for e in exposed) + tuple(e.message for e in exposed_403)
    return PathCheckResult(
        exposed=tuple(exposed),
        findings=findings,
        fetch_ok=fetch_ok,
        exposed_403=tuple(exposed_403),
    )
