"""Vérifications CORS et cross-origin (roadmap §5.4).

Ce module implémente les contrôles décrits dans docs/verifications/cors-et-cross-origin.md :

- **CORS** : requêtes GET et OPTIONS avec en-tête Origin vers la page principale et vers
  des URLs dérivées (chemins sensibles : /api/, /user/, /admin/, etc.). Détection de :
  - Access-Control-Allow-Origin: * sur endpoint sensible ;
  - Access-Control-Allow-Credentials: true avec réflexion d'origine non validée ;
  - Incohérence Credentials + Allow-Origin * ;
  - Méthodes PUT/DELETE/PATCH exposées sans nécessité ;
  - En-têtes sensibles dans Access-Control-Expose-Headers.
- **Mixed content** : détection de ressources en http:// sur une page servie en HTTPS
  (sous-ressources extraites du HTML).
- **CORP** : Cross-Origin-Resource-Policy manquant sur les réponses analysées.

Les requêtes sont effectuées avec un client HTTP partagé. Le nombre d'URLs sensibles
testées est limité par la configuration (sensitive_paths).
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config_loader import get_cors_cross_origin_settings
from app.services.passive.subresources import extract_subresource_urls
from app.utils.headers import get_header_insensitive
from app.utils.url_helpers import build_url_with_path


@dataclass(frozen=True)
class CorsCrossOriginCheckResult:
    """Résultat des vérifications CORS et cross-origin.

    Attributes:
        findings: Messages bruts décrivant les problèmes (ACAO * sensible, réflexion
            d'origine, mixed content, CORP manquant, etc.).
        fetch_ok: True si au moins la page principale a pu être analysée.
    """

    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict[str, Any]:
        """Sérialise pour l'événement SSE result."""
        return {"findings": list(self.findings), "fetch_ok": self.fetch_ok}


def _is_sensitive_url(url: str, sensitive_paths: tuple[str, ...]) -> bool:
    """Indique si l'URL est considérée comme sensible (path contient un fragment)."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return any(fragment and fragment in path for fragment in sensitive_paths)


def _parse_allow_methods(value: str | None) -> set[str]:
    """Extrait les méthodes depuis Access-Control-Allow-Methods (virgules, espaces)."""
    if not value or not value.strip():
        return set()
    return {m.strip().upper() for m in value.split(",") if m.strip()}


def _parse_expose_headers(value: str | None) -> set[str]:
    """Extrait les noms d'en-têtes depuis Access-Control-Expose-Headers."""
    if not value or not value.strip():
        return set()
    return {h.strip() for h in value.split(",") if h.strip()}


def _get_cors_headers(resp: httpx.Response) -> dict[str, str | None]:
    """Récupère les en-têtes CORS d'une réponse (insensible à la casse pour les noms)."""
    return {
        "acao": get_header_insensitive(resp, "Access-Control-Allow-Origin"),
        "acac": get_header_insensitive(resp, "Access-Control-Allow-Credentials"),
        "allow_methods": get_header_insensitive(resp, "Access-Control-Allow-Methods"),
        "expose_headers": get_header_insensitive(resp, "Access-Control-Expose-Headers"),
        "corp": get_header_insensitive(resp, "Cross-Origin-Resource-Policy"),
    }


# Content-Types considérés comme des réponses API (pas une page HTML type 404).
_API_CONTENT_TYPES = (
    "application/json",
    "application/xml",
    "text/xml",
    "application/javascript",
    "application/vnd.",
)


def _response_looks_like_api(resp: httpx.Response | None) -> bool:
    """Indique si la réponse ressemble à une API (JSON, XML, etc.) et non à une page HTML.

    Évite les faux positifs « CORP manquant » sur des chemins sensibles qui renvoient
    en réalité une page « Cette page n'existe pas » (200 + text/html).
    """
    if resp is None:
        return False
    ct = get_header_insensitive(resp, "Content-Type") or ""
    ct_lower = ct.split(";")[0].strip().lower()
    if ct_lower.startswith("text/html"):
        return False
    if any(ct_lower.startswith(prefix) for prefix in _API_CONTENT_TYPES):
        return True
    if resp.status_code == 204:
        return True
    return False


async def _request_with_origin(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    origin: str,
    timeout: float,
) -> httpx.Response | None:
    """Effectue une requête avec l'en-tête Origin. Retourne None en cas d'erreur."""
    try:
        if method.upper() == "GET":
            return await client.get(url, headers={"Origin": origin}, timeout=timeout)
        if method.upper() == "OPTIONS":
            return await client.request(
                "OPTIONS",
                url,
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
                timeout=timeout,
            )
    except Exception:
        pass
    return None


def _merge_cors_from_responses(
    opt_resp: httpx.Response | None,
    get_resp: httpx.Response | None,
) -> dict[str, str | None]:
    """Fusionne les en-têtes CORS des réponses OPTIONS et GET (OPTIONS prioritaire)."""
    cors = _get_cors_headers(opt_resp) if opt_resp else {}
    if not cors.get("acao") and get_resp:
        get_cors = _get_cors_headers(get_resp)
        for k, v in get_cors.items():
            if v is not None and cors.get(k) is None:
                cors[k] = v
    return cors


def _add_findings_acao_and_credentials(
    cors: dict[str, str | None],
    url: str,
    origin: str,
    sensitive_and_like_api: bool,
    findings: list[str],
) -> None:
    """Ajoute les findings ACAO * sur endpoint sensible et Credentials / réflexion."""
    acao = (cors.get("acao") or "").strip()
    acac_raw = (cors.get("acac") or "").strip().lower()
    acac = acac_raw in ("true", "1")
    if sensitive_and_like_api and acao == "*":
        findings.append(f"Access-Control-Allow-Origin: * sur endpoint sensible : {url}.")
    if acac and acao == "*":
        findings.append(
            f"Incohérence CORS (Access-Control-Allow-Credentials: true avec Allow-Origin: *) : {url}.",
        )
    elif acac and acao == origin:
        findings.append(
            f"Réflexion d'origine non validée (Credentials + Origin reflété) : {url}.",
        )


def _add_findings_methods_and_expose(
    cors: dict[str, str | None],
    url: str,
    is_sensitive: bool,
    get_resp: httpx.Response | None,
    settings: Any,
    findings: list[str],
) -> None:
    """Ajoute les findings Allow-Methods et Expose-Headers sensibles."""
    like_api = not is_sensitive or _response_looks_like_api(get_resp)
    allow_methods = _parse_allow_methods(cors.get("allow_methods"))
    dangerous = allow_methods & {"PUT", "DELETE", "PATCH"}
    if dangerous and like_api:
        findings.append(
            f"Méthodes CORS potentiellement dangereuses exposées ({', '.join(sorted(dangerous))}) : {url}.",
        )
    exposed = _parse_expose_headers(cors.get("expose_headers"))
    for sensitive_header in settings.expose_headers_sensitive:
        if sensitive_header in exposed and like_api:
            findings.append(
                f"En-tête sensible exposé via Access-Control-Expose-Headers : {sensitive_header} : {url}.",
            )


async def _check_cors_for_url(
    client: httpx.AsyncClient,
    url: str,
    is_sensitive: bool,
    settings: Any,
    findings: list[str],
) -> None:
    """Analyse les réponses GET et OPTIONS avec Origin et ajoute les findings pour cette URL."""
    timeout = settings.subresource_timeout
    origin = settings.test_origin
    get_resp = await _request_with_origin(client, url, "GET", origin, timeout)
    opt_resp = await _request_with_origin(client, url, "OPTIONS", origin, timeout)
    cors = _merge_cors_from_responses(opt_resp, get_resp)
    sensitive_and_like_api = is_sensitive and _response_looks_like_api(get_resp)

    _add_findings_acao_and_credentials(cors, url, origin, sensitive_and_like_api, findings)
    _add_findings_methods_and_expose(cors, url, is_sensitive, get_resp, settings, findings)

    if not cors.get("corp") and sensitive_and_like_api:
        findings.append(
            f"Cross-Origin-Resource-Policy manquant sur endpoint sensible : {url}.",
        )


async def _check_mixed_content(
    response: httpx.Response,
    base_url: str,
    max_sub: int,
    findings: list[str],
) -> None:
    """Détecte les sous-ressources en http:// sur une page HTTPS."""
    parsed = urlparse(base_url)
    if (parsed.scheme or "").lower() != "https":
        return
    html = response.text or ""
    urls = extract_subresource_urls(html, base_url, max_sub)
    for u in urls:
        if u.strip().lower().startswith("http://"):
            findings.append(
                f"Mixed content : ressource chargée en HTTP sur page HTTPS : {u}.",
            )


async def run_cors_domain_checks(
    base_url: str,
    client: httpx.AsyncClient,
) -> CorsCrossOriginCheckResult:
    """Vérifications CORS au niveau du domaine (chemins sensibles configurés).

    Exécutée une seule fois en mode multi-URL. Sonde tous les chemins sensibles
    (ex. /api/, /admin/, /auth/) indépendamment de la page scannée.

    Args:
        base_url: URL HTTPS de base du domaine (ex. https://example.com/).
        client: Client HTTPX partagé.

    Returns:
        CorsCrossOriginCheckResult: Findings issus des chemins sensibles uniquement.
    """
    findings: list[str] = []
    settings = get_cors_cross_origin_settings()
    base_for_paths = base_url.rstrip("/")

    for path in settings.sensitive_paths:
        if not path.strip():
            continue
        derived = build_url_with_path(base_for_paths, path)
        await _check_cors_for_url(client, derived, is_sensitive=True, settings=settings, findings=findings)

    return CorsCrossOriginCheckResult(findings=tuple(findings), fetch_ok=True)


async def run_cors_page_checks(
    response: httpx.Response | None,
    page_url: str,
    client: httpx.AsyncClient,
    domain_result: CorsCrossOriginCheckResult | None = None,
) -> CorsCrossOriginCheckResult:
    """Vérifications CORS spécifiques à une page (utilisé en mode multi-URL).

    Vérifie uniquement la page fournie (GET+OPTIONS avec Origin, CORP, mixed content).
    Les findings du domaine (chemins sensibles) sont injectés depuis domain_result.

    Args:
        response: Réponse HTTP de la page à analyser.
        page_url: URL de la page.
        client: Client HTTPX partagé.
        domain_result: Résultat des checks domaine à fusionner (optionnel).

    Returns:
        CorsCrossOriginCheckResult: Findings page + domaine fusionnés.
    """
    findings: list[str] = list(domain_result.findings if domain_result else [])
    settings = get_cors_cross_origin_settings()

    if response is None:
        findings.append("CORS et cross-origin inaccessibles : réponse HTTPS indisponible.")
        return CorsCrossOriginCheckResult(findings=tuple(findings), fetch_ok=False)

    is_sensitive = _is_sensitive_url(page_url, settings.sensitive_paths)
    await _check_cors_for_url(client, page_url, is_sensitive=is_sensitive, settings=settings, findings=findings)

    if not is_sensitive:
        corp = get_header_insensitive(response, "Cross-Origin-Resource-Policy")
        if not corp:
            findings.append("Cross-Origin-Resource-Policy manquant sur la page principale.")

    await _check_mixed_content(response, page_url, settings.max_sub_resources, findings)

    return CorsCrossOriginCheckResult(findings=tuple(findings), fetch_ok=True)


async def run_cors_cross_origin_checks(
    response: httpx.Response | None,
    https_url: str,
    client: httpx.AsyncClient,
) -> CorsCrossOriginCheckResult:
    """Exécute les vérifications CORS et cross-origin.

    - Envoie des requêtes GET et OPTIONS avec l'en-tête Origin vers la page principale
      et vers chaque URL dérivée (base + chemin sensible). Analyse ACAO, ACAC,
      Allow-Methods, Expose-Headers, CORP.
    - Sur la page principale (HTML), extrait les sous-ressources et signale le mixed content.
    - Referrer-Policy n'est pas vérifié ici ; il l'est dans la catégorie Security Headers.
      Le résumé de la catégorie CORS indique que Referrer-Policy est vérifié côté headers.

    Args:
        response: Réponse HTTPS de la page principale (ou None si fetch échoué).
        https_url: URL HTTPS de base du scan.
        client: Client HTTPX partagé.

    Returns:
        CorsCrossOriginCheckResult: Résultat agrégé.
    """
    findings: list[str] = []
    settings = get_cors_cross_origin_settings()

    if response is None:
        findings.append("CORS et cross-origin inaccessibles : réponse HTTPS indisponible.")
        return CorsCrossOriginCheckResult(findings=tuple(findings), fetch_ok=False)

    page_url = str(response.url) if getattr(response, "url", None) else https_url
    base_for_paths = page_url.rstrip("/") or page_url

    # Liste des URLs à tester : page principale + chemins sensibles
    urls_to_check: list[tuple[str, bool]] = [(page_url, _is_sensitive_url(page_url, settings.sensitive_paths))]
    for path in settings.sensitive_paths:
        if not path.strip():
            continue
        derived = build_url_with_path(base_for_paths, path)
        if derived not in (u[0] for u in urls_to_check):
            urls_to_check.append((derived, True))

    for url, is_sensitive in urls_to_check:
        await _check_cors_for_url(client, url, is_sensitive, settings, findings)

    # CORP manquant sur page principale (uniquement si page non sensible, pour éviter doublon)
    main_is_sensitive = _is_sensitive_url(page_url, settings.sensitive_paths)
    if not main_is_sensitive:
        corp = get_header_insensitive(response, "Cross-Origin-Resource-Policy")
        if not corp:
            findings.append(
                "Cross-Origin-Resource-Policy manquant sur la page principale.",
            )

    # Mixed content (uniquement sur page principale en HTTPS)
    await _check_mixed_content(
        response,
        page_url,
        settings.max_sub_resources,
        findings,
    )

    return CorsCrossOriginCheckResult(findings=tuple(findings), fetch_ok=True)
