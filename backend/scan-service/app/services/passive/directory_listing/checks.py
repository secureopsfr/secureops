"""Détection du directory listing (roadmap §3.5).

Teste une liste de répertoires usuels (/uploads/, /assets/, /static/, /tmp/, /logs/, etc.)
et détecte si le serveur renvoie une page de listing (signatures Apache/Nginx ou listing partiel).
Gère aussi les 403 sur chemins sensibles (existence révélée).
"""

import re

from app.config_loader import (
    get_directory_listing_max_body,
    get_directory_listing_partial_extensions,
    get_directory_listing_partial_min_links,
    get_directory_listing_sensitive_403_paths,
    get_directory_listing_settings,
)
from app.services.passive.path_checks import PathCheckResult, PathFinding, run_path_checks


def _make_on_403_handler():
    """Retourne le callback pour les 403 sur chemins sensibles."""
    sensitive_paths = frozenset((p.rstrip("/") + "/") if p else "/" for p in get_directory_listing_sensitive_403_paths())

    def handler(path: str) -> PathFinding | None:
        path_norm = (path.rstrip("/") + "/") if path else "/"
        if path_norm in sensitive_paths:
            return PathFinding(
                path=path,
                severity="medium",
                message=f"Répertoire sensible {path} retourne 403 : existence révélée.",
            )
        return None

    return handler


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
    partial_extensions = get_directory_listing_partial_extensions()
    min_links = get_directory_listing_partial_min_links()
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
        if any(href.endswith(ext) for ext in partial_extensions):
            count += 1
            continue
        # Lien relatif simple (ex. "fichier.pdf" ou "sous-dossier/")
        if "/" not in href and "." in href:
            count += 1
    return count >= min_links


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
    return await run_path_checks(
        base_url,
        configs,
        _is_listing_body,
        max_body,
        client=client,
        on_403=_make_on_403_handler(),
    )
