"""Détection du directory listing (roadmap §3.5).

Teste une liste de répertoires usuels (/uploads/, /assets/, /static/) et détecte
si le serveur renvoie une page de listing (signatures Apache/Nginx).
"""

from app.config_loader import get_directory_listing_max_body, get_directory_listing_settings
from app.services.path_checks import PathCheckResult, run_path_checks
from app.utils.url_helpers import build_https_url


def _is_listing_body(body: bytes, _path: str) -> bool:
    """Détecte si le corps correspond à une page de listing Apache/Nginx.

    Signatures typiques : Index of, Parent Directory, [DIR], mod_autoindex (Apache),
    nginx, <a href=" (Nginx). Évite les faux positifs en exigeant plusieurs motifs.

    Args:
        body: Corps de la réponse HTTP (octets).
        _path: Chemin testé (non utilisé, signature identique pour tous).

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


async def run_directory_listing_checks(
    base_url: str,
    *,
    client=None,
) -> PathCheckResult:
    """Teste tous les répertoires configurés pour le directory listing.

    Effectue des requêtes GET en parallèle. Un répertoire est considéré vulnérable
    si status 200 et contenu contient les signatures Apache/Nginx de listing.
    Si client est fourni, réutilise la connexion TCP (keep-alive).

    Args:
        base_url: URL de base (ex. https://example.com/).
        client: Client httpx optionnel (issu de scan_client()) pour réutilisation.

    Returns:
        PathCheckResult: Répertoires exposés et findings.
    """
    https_base = build_https_url(base_url)
    configs = get_directory_listing_settings()
    max_body = get_directory_listing_max_body()
    return await run_path_checks(https_base, configs, _is_listing_body, max_body, client=client)
