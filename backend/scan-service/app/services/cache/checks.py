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
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config_loader import CacheSettings, get_cache_settings
from app.services.subresources import extract_subresource_urls
from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class CacheCheckResult:
    """Résultat des vérifications Cache et performances.

    Attributes:
        findings (tuple[str, ...]): Messages bruts décrivant les problèmes
            détectés (page sensible cacheable, incohérence Pragma, asset
            immuable sans cache long, etc.).
        fetch_ok (bool): Indique si les en-têtes de la page principale ont été
            analysés correctement. False en cas d'erreur bloquante.
        sub_resources_checked (int): Nombre de sous-ressources (scripts, CSS,
            images) effectivement analysées.
        sub_resources_with_issues (int): Nombre de sous-ressources pour
            lesquelles une configuration de cache sous-optimale a été détectée.
    """

    findings: tuple[str, ...]
    fetch_ok: bool
    sub_resources_checked: int = 0
    sub_resources_with_issues: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le résultat pour l'événement SSE result.

        Returns:
            dict[str, Any]: Représentation sérialisable du résultat.
        """
        return {
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
            "sub_resources_checked": self.sub_resources_checked,
            "sub_resources_with_issues": self.sub_resources_with_issues,
        }


def _is_sensitive_url(url: str, sensitive_paths: tuple[str, ...]) -> bool:
    """Détermine si l'URL fournie correspond à une page sensible.

    La détection est purement basée sur le chemin de l'URL (pas de crawling) :
    si l'un des fragments configurés dans ``sensitive_paths`` apparaît dans le
    chemin, la page est considérée comme sensible.

    Args:
        url: URL complète de la page (ex. https://example.com/login).
        sensitive_paths: Fragments de chemin à rechercher (ex. /login, /admin).

    Returns:
        bool: True si la page est considérée comme sensible, False sinon.
    """
    parsed = urlparse(url)
    path = parsed.path or "/"
    return any(fragment and fragment in path for fragment in sensitive_paths)


def _parse_max_age(cache_control: str) -> int | None:
    """Extrait la directive max-age en secondes depuis un Cache-Control.

    Args:
        cache_control: Valeur brute de l'en-tête Cache-Control.

    Returns:
        int | None: Valeur de max-age en secondes si trouvée, sinon None.
    """
    parts = cache_control.split(",")
    for part in parts:
        token = part.strip().lower()
        if token.startswith("max-age="):
            try:
                return int(token.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


async def _analyze_subresources(
    response: httpx.Response,
    client: httpx.AsyncClient,
    cache_settings: CacheSettings,
    findings: list[str],
) -> tuple[int, int]:
    """Analyse les sous-ressources de la page (scripts, CSS, images).

    Args:
        response: Réponse HTTP de la page principale.
        client: Client HTTPX partagé pour réutiliser les connexions.
        settings: Paramètres cache (résultat de get_cache_settings()).
        findings: Liste mutable de messages de findings à enrichir.

    Returns:
        tuple[int, int]: (nombre de sous-ressources analysées,
        nombre de sous-ressources avec configuration de cache sous-optimale).
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
    issues = 0

    for url in urls:
        checked += 1
        try:
            head_resp = await client.head(url, timeout=sub_timeout)
            # Certains serveurs ne supportent pas HEAD correctement.
            if head_resp.status_code in (405, 501):
                resp = await client.get(url, timeout=sub_timeout)
            else:
                resp = head_resp
        except Exception:
            # On ignore silencieusement les erreurs sur les sous-ressources.
            continue

        cache_control = get_header_insensitive(resp, "Cache-Control")
        if not cache_control:
            continue

        # Asset immuable : URL contenant un hash (pattern configurable).
        if immutable_pattern and re.search(immutable_pattern, url):
            cc_lower = cache_control.lower()
            has_immutable = "immutable" in cc_lower
            max_age = _parse_max_age(cc_lower)
            if not has_immutable or max_age is None or max_age < immutable_max_age:
                issues += 1
                findings.append(
                    f"Asset immuable sans cache long détecté : {url} (Cache-Control='{cache_control}').",
                )

    return checked, issues


async def check_cache_from_response(
    response: httpx.Response | None,
    https_url: str,
    client: httpx.AsyncClient,
) -> CacheCheckResult:
    """Vérifie la configuration de cache de la page principale et des sous-ressources.

    Cette fonction ne réalise aucun crawling : elle se limite à la page fournie
    (URL scannée) et aux sous-ressources déclarées dans le HTML (scripts, CSS,
    images).

    Args:
        response: Réponse HTTP de la page principale (ou None si le fetch a échoué).
        https_url: URL HTTPS normalisée utilisée pour le scan.
        client: Client HTTPX partagé pour exécuter les requêtes HEAD/GET sur les
            sous-ressources.

    Returns:
        CacheCheckResult: Résultat agrégé des vérifications cache.
    """
    findings: list[str] = []

    if response is None:
        findings.append("En-têtes de cache inaccessibles : réponse HTTPS indisponible.")
        return CacheCheckResult(findings=tuple(findings), fetch_ok=False)

    cache_settings = get_cache_settings()
    page_url = str(response.url) if getattr(response, "url", None) else https_url

    cache_control = get_header_insensitive(response, "Cache-Control")
    pragma = get_header_insensitive(response, "Pragma")

    if _is_sensitive_url(page_url, cache_settings.sensitive_paths):
        if cache_control is None:
            findings.append("Page sensible sans en-tête Cache-Control explicite.")
        else:
            cc_lower = cache_control.lower()
            is_private_or_nostore = "no-store" in cc_lower or "private" in cc_lower or "no-cache" in cc_lower
            max_age = _parse_max_age(cc_lower)
            is_public = "public" in cc_lower
            if not is_private_or_nostore and (is_public or (max_age is not None and max_age > cache_settings.sensitive_max_age)):
                findings.append(
                    f"Page sensible cacheable publiquement : Cache-Control='{cache_control}'.",
                )

    if pragma is not None and cache_control is not None:
        pragma_lower = pragma.lower()
        cc_lower = cache_control.lower()
        if "no-cache" in pragma_lower and ("max-age" in cc_lower or "public" in cc_lower):
            findings.append(
                f"Incohérence Pragma/Cache-Control : Pragma='{pragma}', Cache-Control='{cache_control}'.",
            )

    sub_checked = 0
    sub_issues = 0
    with contextlib.suppress(Exception):
        sub_checked, sub_issues = await _analyze_subresources(
            response=response,
            client=client,
            cache_settings=cache_settings,
            findings=findings,
        )

    return CacheCheckResult(
        findings=tuple(findings),
        fetch_ok=True,
        sub_resources_checked=sub_checked,
        sub_resources_with_issues=sub_issues,
    )
