"""Détection des fichiers sensibles et endpoints exposés (roadmap §3.4).

Teste une liste fixe de chemins (/.env, /.git/config, etc.) et détecte l'exposition
quand status 200 + contenu correspond aux signatures connues.
"""

import re

from app.config_loader import get_exposed_files_max_body, get_exposed_files_settings
from app.services.path_checks import PathCheckResult, run_path_checks


def _content_matches_env(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à un .env (KEY=value, DATABASE_, SECRET_, etc.)."""
    text = body.decode("utf-8", errors="replace").lower()
    if not re.search(r"^[a-z0-9_]+=.*$", text[:200], re.MULTILINE | re.IGNORECASE):
        return False
    return any(kw in text for kw in ("database_url", "secret_key", "api_key", "password", "db_password"))


def _content_matches_git_config(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à .git/config."""
    text = body.decode("utf-8", errors="replace").lower()
    return "[core]" in text or "[remote" in text or "repositoryformatversion" in text


def _content_matches_zip(body: bytes, _path: str) -> bool:
    """Vérifie si le corps est un fichier ZIP (commence par PK)."""
    return len(body) > 0 and body[:2] == b"PK"


def _content_matches_phpinfo(body: bytes, _path: str) -> bool:
    """Vérifie si le corps contient la sortie phpinfo."""
    text = body.decode("utf-8", errors="replace").lower()
    return "phpinfo" in text and ("php version" in text or "configuration" in text)


def _content_matches_admin(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à une page admin (formulaire login)."""
    text = body.decode("utf-8", errors="replace").lower()
    has_form = "form" in text and ("password" in text or "passwd" in text)
    has_login = "login" in text or "username" in text or "administrator" in text
    return has_form or (has_login and len(body) > 500)


def _content_matches_ds_store(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à .DS_Store (Bud1, DSDB)."""
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
    """Retourne le checker de signature pour un chemin (normalisé)."""
    path_normalized = path.rstrip("/") if path != "/" else path
    key = path_normalized.lower()
    if key in _SIGNATURE_CHECKERS:
        return _SIGNATURE_CHECKERS[key]
    if path_normalized == "/.git/config":
        return _content_matches_git_config
    return None


def _body_checker(body: bytes, path: str) -> bool:
    """Dispatcher vers le checker approprié pour exposed_files."""
    checker = _get_checker_for_path(path)
    if checker is None:
        return False
    return checker(body, path)


async def run_exposed_files_checks(
    base_url: str,
    *,
    client=None,
) -> PathCheckResult:
    """Teste tous les chemins sensibles configurés pour l'exposition.

    Effectue des requêtes GET en parallèle. Un chemin est considéré exposé si
    status 200 et contenu correspond aux signatures connues. Si client est fourni,
    réutilise la connexion TCP (keep-alive).

    Args:
        base_url: URL de base HTTPS (ex. https://example.com/). L'appelant fournit déjà ctx.https_url.
        client: Client httpx optionnel (issu de scan_client()) pour réutilisation.

    Returns:
        PathCheckResult: Chemins exposés et findings.
    """
    configs = get_exposed_files_settings()
    max_body = get_exposed_files_max_body()
    return await run_path_checks(base_url, configs, _body_checker, max_body, client=client)
