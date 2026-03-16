"""Exécution des checks de niveau page — partagée entre scan single-URL et multi-URL.

Chaque page scannée passe par run_page_checks(), quelle que soit la variante de scan.
Ajouter un nouveau check de niveau page ici suffit ; l'orchestrateur multi-URL et les
lambdas SCAN_STEPS peuvent s'appuyer sur cette liste canonique.

Checks passifs (aucune requête HTTP) :
    headers, cookies, tech_fingerprinting, information_disclosure, integrity

Checks actifs (requêtes HTTP taggées) :
    cache (HEAD/GET assets), cors_cross_origin (GET/OPTIONS)
"""

from __future__ import annotations

from typing import Any

import httpx

from app.services.passive.both.cache import checks as cache_checks
from app.services.passive.both.cookies import check_cookies_from_response
from app.services.passive.both.cors_cross_origin.checks import run_cors_page_checks
from app.services.passive.both.information_disclosure import check_information_disclosure_from_response
from app.services.passive.both.security_headers import check_security_headers_from_response
from app.services.passive.both.tech_fingerprinting import check_tech_fingerprinting_from_response
from app.services.passive.frontend.integrity import check_integrity_from_response
from app.utils.http_fetch import http_request_category


async def run_page_checks(
    response: httpx.Response,
    url: str,
    client: httpx.AsyncClient,
    *,
    assets_cache: dict[str, str | None] | None = None,
    is_https: bool = True,
    domain_cors_result: object = None,
) -> dict[str, Any]:
    """Exécute les 7 checks de niveau page et retourne leurs résultats.

    Source unique pour la liste des checks page. Tout ajout ou suppression de
    check page se fait ici uniquement ; ni l'orchestrateur multi-URL ni le
    scan single-URL n'ont besoin d'être modifiés.

    Args:
        response: Réponse HTTP de la page à analyser.
        url: URL complète de la page.
        client: Client httpx partagé du scan (keep-alive).
        assets_cache: Cache d'assets partagé entre pages (optimisation multi-URL).
            None -> comportement standard sans mutualisation.
        is_https: True si la page est servie en HTTPS (pour le check cookies Secure).
        domain_cors_result: Résultat CORS domaine pré-calculé (multi-URL uniquement).
            None -> les checks CORS page opèrent sans contexte domaine.

    Returns:
        dict keyed par nom de check : "headers", "cookies", "tech_fingerprinting",
        "information_disclosure", "integrity", "cache", "cors_cross_origin".
    """
    results: dict[str, Any] = {}

    # -- Checks passifs (aucune requête HTTP) ---------------------------------
    results["headers"] = check_security_headers_from_response(response)
    results["cookies"] = check_cookies_from_response(response, is_https=is_https)
    results["tech_fingerprinting"] = check_tech_fingerprinting_from_response(response)
    results["information_disclosure"] = check_information_disclosure_from_response(response)
    results["integrity"] = check_integrity_from_response(response, url)

    # -- Checks actifs (requêtes HTTP taggées pour comptage) ------------------
    with http_request_category("cache"):
        results["cache"] = await cache_checks.check_cache_from_response(response, url, client, assets_cache=assets_cache)
    with http_request_category("cors_cross_origin"):
        results["cors_cross_origin"] = await run_cors_page_checks(response, url, client, domain_result=domain_cors_result)

    return results
