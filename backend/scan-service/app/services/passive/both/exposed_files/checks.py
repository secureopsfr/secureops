"""Détection des fichiers sensibles et endpoints exposés (roadmap §3.4).

Teste une liste fixe de chemins (/.env, /.git/config, etc.) et détecte l'exposition
quand status 200 + contenu correspond aux signatures connues.
"""

import re

from app.config_loader import get_exposed_files_max_body, get_exposed_files_settings
from app.services.passive.both.path_checks import PathCheckResult, run_path_checks


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


def _content_matches_htaccess(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à .htaccess (Apache)."""
    text = body.decode("utf-8", errors="replace").lower()
    return "rewriterule" in text or "order" in text or "allow" in text or "deny" in text


def _content_matches_web_config(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à web.config (XML IIS)."""
    text = body.decode("utf-8", errors="replace").lower()
    return "<configuration" in text or "<system.webserver" in text


def _content_matches_svn_entries(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à .svn/entries."""
    text = body.decode("utf-8", errors="replace")
    return "dir" in text[:50] or "file" in text[:50] or "10" in text[:20]


def _content_matches_json_package(body: bytes, _path: str) -> bool:
    """Vérifie si le corps est un JSON de type package (composer.json ou package.json)."""
    text = body.decode("utf-8", errors="replace").lower()
    if "{" not in text or "}" not in text:
        return False
    return '"name"' in text and ("require" in text or "dependencies" in text)


def _content_matches_npmrc(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à .npmrc (registry=, auth=)."""
    text = body.decode("utf-8", errors="replace").lower()
    return "registry=" in text or "auth=" in text or "_auth=" in text


def _content_matches_backup_config(body: bytes, _path: str) -> bool:
    """Vérifie si le corps ressemble à un fichier de config (backup)."""
    text = body.decode("utf-8", errors="replace").lower()
    if "database" in text or "secret" in text or "password" in text:
        return True
    if "<configuration" in text or "rewriterule" in text:
        return True
    return False


def _content_matches_openapi(body: bytes, _path: str) -> bool:
    """Vérifie si le corps est Swagger/OpenAPI (JSON ou HTML Swagger UI)."""
    text = body.decode("utf-8", errors="replace").lower()
    if '"openapi"' in text or '"swagger"' in text:
        return True
    if "swagger" in text and ("paths" in text or "api" in text):
        return True
    return False


def _content_matches_graphql(body: bytes, _path: str) -> bool:
    """Vérifie si le corps suggère un endpoint GraphQL (JSON avec data/errors/__schema)."""
    text = body.decode("utf-8", errors="replace").lower()
    if "{" not in text:
        return False
    return '"data"' in text or '"errors"' in text or '"__schema"' in text or '"querytype"' in text


def _content_matches_generic_sensitive(body: bytes, _path: str) -> bool:
    """Checker générique pour chemins non mappés : détecte contenu sensible typique.

    Utilisé en fallback quand un chemin de settings.yml n'a pas de signature dédiée.
    Recherche des motifs courants (secrets, config, credentials).
    """
    if len(body) < 20:
        return False
    text = body.decode("utf-8", errors="replace").lower()
    sensitive_keywords = (
        "database_url",
        "secret_key",
        "api_key",
        "password",
        "db_password",
        "aws_secret",
        "private_key",
        "token",
        "credential",
    )
    if any(kw in text for kw in sensitive_keywords):
        return True
    env_like = "=" in text and re.search(r"^[a-z0-9_]+=.*$", text[:500], re.MULTILINE | re.IGNORECASE)
    if env_like and any(kw in text[:1000] for kw in ("secret", "pass", "key", "token")):
        return True
    if "{" in text and "}" in text and ('"password"' in text or '"secret"' in text or '"api_key"' in text):
        return True
    return False


def _get_signature_checker(path: str):
    """Retourne le checker de signature pour un chemin (normalisé)."""
    path_norm = path.rstrip("/") if path != "/" else path
    key = path_norm.lower()
    # Mapping explicite par chemin
    checkers = {
        "/.env": _content_matches_env,
        "/.git/config": _content_matches_git_config,
        "/backup.zip": _content_matches_zip,
        "/phpinfo.php": _content_matches_phpinfo,
        "/admin/": _content_matches_admin,
        "/.ds_store": _content_matches_ds_store,
        "/.htaccess": _content_matches_htaccess,
        "/web.config": _content_matches_web_config,
        "/.svn/entries": _content_matches_svn_entries,
        "/composer.json": _content_matches_json_package,
        "/package.json": _content_matches_json_package,
        "/.npmrc": _content_matches_npmrc,
        "/config.bak": _content_matches_backup_config,
        "/web.config.bak": _content_matches_backup_config,
        "/.env.bak": _content_matches_env,  # Même signature que .env
        "/swagger": _content_matches_openapi,
        "/swagger.json": _content_matches_openapi,
        "/api-docs": _content_matches_openapi,
        "/api-docs.json": _content_matches_openapi,
        "/graphql": _content_matches_graphql,
    }
    return checkers.get(key)


def _body_checker(body: bytes, path: str) -> bool:
    """Dispatcher vers le checker approprié pour exposed_files.

    Utilise le mapping par chemin si disponible, sinon le checker générique.
    """
    checker = _get_signature_checker(path)
    if checker is not None:
        return checker(body, path)
    return _content_matches_generic_sensitive(body, path)


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
