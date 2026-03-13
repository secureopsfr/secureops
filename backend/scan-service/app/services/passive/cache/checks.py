"""Vérifications Cache et performances (roadmap §5.3.1 et §5.3.2).

Ce module implémente les contrôles suivants, tels que décrits dans
``docs/verifications/cache-et-performances.md`` :

- analyse des en-têtes de cache de la page principale :
  - présence et directives de ``Cache-Control`` ;
  - cohérence avec ``Pragma: no-cache`` ;
  - détection des pages sensibles (login, admin, API) cacheables publiquement ;
- analyse d'un sous-ensemble de sous-ressources (scripts, CSS, images) :
  - récupération des headers via HEAD (puis GET en fallback si nécessaire) ;
  - détection des assets immuables sans cache long
    (``max-age`` insuffisant ou absence de ``immutable``).

Les tests restent non intrusifs : seules des requêtes HEAD/GET sont effectuées
sur la page principale et les sous-ressources découvertes dans le HTML.
"""

import contextlib
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config_loader import CacheSettings, get_cache_settings
from app.services.passive.subresources import extract_subresource_urls
from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class CacheIssue:
    """Issue de cache typée pour une normalisation sans correspondance de chaînes.

    Attributes:
        kind: Discriminant sémantique du problème détecté.
            Valeurs possibles : "sensitive_public", "no_cache_control",
            "pragma_incoherent", "immutable_bad_cache".
        message: Message lisible pour l'affichage SSE et le rapport.
    """

    kind: str
    message: str


@dataclass(frozen=True)
class CacheCheckResult:
    """Résultat des vérifications Cache et performances.

    Attributes:
        findings (tuple[str, ...]): Messages bruts pour la sérialisation SSE
            (compat ascendante). Dérivés des ``issues``.
        fetch_ok (bool): Indique si les en-têtes de la page principale ont été
            analysés correctement. False en cas d'erreur bloquante.
        issues (tuple[CacheIssue, ...]): Issues typées consommées par le normalizer
            sans correspondance de chaînes.
        sub_resources_checked (int): Nombre de sous-ressources analysées.
        sub_resources_with_issues (int): Nombre de sous-ressources avec problème de cache.
    """

    findings: tuple[str, ...]
    fetch_ok: bool
    issues: tuple[CacheIssue, ...] = field(default=())
    sub_resources_checked: int = 0
    sub_resources_with_issues: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le résultat pour l'événement SSE result."""
        return {
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
            "sub_resources_checked": self.sub_resources_checked,
            "sub_resources_with_issues": self.sub_resources_with_issues,
        }


def _is_sensitive_url(url: str, sensitive_paths: tuple[str, ...]) -> bool:
    """Détermine si l'URL fournie correspond à une page sensible."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return any(fragment and fragment in path for fragment in sensitive_paths)


def _parse_max_age(cache_control: str) -> int | None:
    """Extrait la directive max-age en secondes depuis un Cache-Control."""
    parts = cache_control.split(",")
    for part in parts:
        token = part.strip().lower()
        if token.startswith("max-age="):
            try:
                return int(token.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


async def _get_subresource_cache_control(
    *,
    url: str,
    client: httpx.AsyncClient,
    timeout: float,
    assets_cache: dict[str, str | None] | None,
) -> str | None:
    """Récupère Cache-Control d'une sous-ressource (cache partagé + HEAD/GET)."""
    if assets_cache is not None and url in assets_cache:
        return assets_cache[url]

    try:
        head_resp = await client.head(url, timeout=timeout)
        resp = await client.get(url, timeout=timeout) if head_resp.status_code in (405, 501) else head_resp
        cache_control = get_header_insensitive(resp, "Cache-Control")
    except Exception:
        if assets_cache is not None:
            assets_cache[url] = None
        return None

    if assets_cache is not None:
        assets_cache[url] = cache_control
    return cache_control


def _is_bad_immutable_cache(
    *,
    url: str,
    cache_control: str,
    immutable_pattern: str,
    immutable_max_age: int,
) -> bool:
    """Retourne True si un asset immuable n'a pas un cache long correct."""
    if not immutable_pattern or not re.search(immutable_pattern, url):
        return False
    cc_lower = cache_control.lower()
    has_immutable = "immutable" in cc_lower
    max_age = _parse_max_age(cc_lower)
    return (not has_immutable) or max_age is None or max_age < immutable_max_age


async def _analyze_subresources(
    response: httpx.Response,
    client: httpx.AsyncClient,
    cache_settings: CacheSettings,
    issues: list[CacheIssue],
    assets_cache: dict[str, str | None] | None = None,
) -> tuple[int, int]:
    """Analyse les sous-ressources de la page (scripts, CSS, images).

    Args:
        response: Réponse HTTP de la page principale.
        client: Client HTTPX partagé pour réutiliser les connexions.
        cache_settings: Paramètres cache (résultat de get_cache_settings()).
        issues: Liste mutable d'issues à enrichir.
        assets_cache: Cache partagé entre pages (multi-URL).

    Returns:
        tuple[int, int]: (sous-ressources analysées, sous-ressources avec problème).
    """
    html = response.text or ""
    max_sub_resources = getattr(cache_settings, "max_sub_resources", 0)
    sub_timeout = getattr(cache_settings, "subresource_timeout", 3.0)
    immutable_pattern = getattr(cache_settings, "immutable_pattern", "")
    immutable_max_age = int(getattr(cache_settings, "immutable_max_age", 31536000))

    urls = extract_subresource_urls(html, str(response.url), max_sub_resources)
    if not urls:
        return 0, 0

    checked = 0
    detected = 0

    for url in urls:
        checked += 1
        cache_control = await _get_subresource_cache_control(
            url=url,
            client=client,
            timeout=sub_timeout,
            assets_cache=assets_cache,
        )

        if not cache_control:
            continue

        if _is_bad_immutable_cache(
            url=url,
            cache_control=cache_control,
            immutable_pattern=immutable_pattern,
            immutable_max_age=immutable_max_age,
        ):
            detected += 1
            msg = f"Asset immuable sans cache long détecté : {url} (Cache-Control='{cache_control}')."
            issues.append(CacheIssue(kind="immutable_bad_cache", message=msg))

    return checked, detected


async def check_cache_from_response(
    response: httpx.Response | None,
    https_url: str,
    client: httpx.AsyncClient,
    assets_cache: dict[str, str | None] | None = None,
) -> CacheCheckResult:
    """Vérifie la configuration de cache de la page principale et des sous-ressources.

    Args:
        response: Réponse HTTP de la page principale (ou None si le fetch a échoué).
        https_url: URL HTTPS normalisée utilisée pour le scan.
        client: Client HTTPX partagé pour exécuter les requêtes HEAD/GET sur les
            sous-ressources.
        assets_cache: Cache partagé entre pages (mode multi-URL).

    Returns:
        CacheCheckResult: Résultat agrégé des vérifications cache.
    """
    issues: list[CacheIssue] = []

    if response is None:
        msg = "En-têtes de cache inaccessibles : réponse HTTPS indisponible."
        issues.append(CacheIssue(kind="connection_failed", message=msg))
        return CacheCheckResult(findings=(msg,), fetch_ok=False, issues=tuple(issues))

    cache_settings = get_cache_settings()
    page_url = str(response.url) if getattr(response, "url", None) else https_url

    cache_control = get_header_insensitive(response, "Cache-Control")
    pragma = get_header_insensitive(response, "Pragma")

    if _is_sensitive_url(page_url, cache_settings.sensitive_paths):
        if cache_control is None:
            msg = "Page sensible sans en-tête Cache-Control explicite."
            issues.append(CacheIssue(kind="no_cache_control", message=msg))
        else:
            cc_lower = cache_control.lower()
            is_private_or_nostore = "no-store" in cc_lower or "private" in cc_lower or "no-cache" in cc_lower
            max_age = _parse_max_age(cc_lower)
            is_public = "public" in cc_lower
            if not is_private_or_nostore and (is_public or (max_age is not None and max_age > cache_settings.sensitive_max_age)):
                msg = f"Page sensible cacheable publiquement : Cache-Control='{cache_control}'."
                issues.append(CacheIssue(kind="sensitive_public", message=msg))

    if pragma is not None and cache_control is not None:
        pragma_lower = pragma.lower()
        cc_lower = cache_control.lower()
        if "no-cache" in pragma_lower and ("max-age" in cc_lower or "public" in cc_lower):
            msg = f"Incohérence Pragma/Cache-Control : Pragma='{pragma}', Cache-Control='{cache_control}'."
            issues.append(CacheIssue(kind="pragma_incoherent", message=msg))

    sub_checked = 0
    sub_issues = 0
    with contextlib.suppress(Exception):
        sub_checked, sub_issues = await _analyze_subresources(
            response=response,
            client=client,
            cache_settings=cache_settings,
            issues=issues,
            assets_cache=assets_cache,
        )

    findings = tuple(issue.message for issue in issues)
    return CacheCheckResult(
        findings=findings,
        fetch_ok=True,
        issues=tuple(issues),
        sub_resources_checked=sub_checked,
        sub_resources_with_issues=sub_issues,
    )
