"""Module de détection des redirections ouvertes.

Utilisé par :
- open_redirect/check.py (Phase A)
- oauth_oidc/check.py (Phase C, paramètre redirect_uri)
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_REDIRECT_PARAMS, inject_query_param

# Payloads de redirection (domaine distinct du scope)
_EVIL_PAYLOADS: list[str] = [
    "https://evil.test",
    "//evil.test",
    "https://evil.test%2F@{target_host}",
    "%68ttps://evil.test",
]


def _is_external_domain(location: str, target_host: str) -> bool:
    """Vérifie si une URL de redirection pointe vers un domaine différent de la cible."""
    if not location:
        return False
    # Normaliser les redirections relatives en absolues
    if location.startswith("//"):
        location = "https:" + location
    parsed = urlparse(location)
    netloc = (parsed.netloc or "").lower().split(":")[0]
    if not netloc:
        return False
    return target_host.lower() not in netloc


async def probe_open_redirect(
    client: IntrusiveHTTPClient,
    url: str,
    param_name: str,
    target_host: str,
) -> str | None:
    """Injecte des payloads de redirection et retourne le domaine externe détecté.

    Args:
        client: Client HTTP configuré avec credentials.
        url: URL de base à tester.
        param_name: Nom du paramètre à injecter.
        target_host: Hostname de la cible (pour détecter les redirections externes).

    Returns:
        L'URL externe de redirection si détectée, None sinon.
    """
    for evil in _EVIL_PAYLOADS:
        payload = evil.replace("{target_host}", target_host)
        probe_url = inject_query_param(url, param_name, payload)
        result = await client.get(probe_url, follow_redirects=False)
        if result.error:
            continue

        # Vérifier Location header (redirection 3xx)
        location = result.location()
        if result.is_redirect and location and _is_external_domain(location, target_host):
            return location

        # Vérifier si suivi de redirections amène sur domaine externe
        if result.final_url and _is_external_domain(result.final_url, target_host):
            return result.final_url

    return None


async def probe_redirect_uri(
    client: IntrusiveHTTPClient,
    url: str,
    target_host: str,
) -> str | None:
    """Teste un paramètre redirect_uri OAuth avec des domaines externes."""
    for param in ["redirect_uri", "redirect_url", "callback"]:
        result = await probe_open_redirect(client, url, param, target_host)
        if result:
            return result
    return None


def get_redirect_candidate_params(url: str, html_body: str, scan_type: str) -> list[str]:
    """Retourne les noms de paramètres candidats pour tester les redirections.

    Pour frontend : paramètres depuis le HTML + query string.
    Pour backend  : query string + liste commune.
    """
    from app.services.intrusive.lib.param_extractor import extract_html_params, extract_query_params

    candidates: set[str] = set(COMMON_REDIRECT_PARAMS)

    # Paramètres query string de l'URL
    for p in extract_query_params(url):
        candidates.add(p.name)

    # Pour frontend, paramètres HTML en plus
    if scan_type == "frontend" and html_body:
        for p in extract_html_params(html_body, url):
            candidates.add(p.name)

    return list(candidates)
