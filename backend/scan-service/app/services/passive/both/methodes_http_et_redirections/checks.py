"""Vérifications Méthodes HTTP et redirections.

Réutilise methodes_data (Allow, ACAM) du module CORS. Effectue TRACE, HEAD,
analyse chaîne de redirections et 301/302 sur formulaires sensibles.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config_loader import get_cors_cross_origin_settings, get_methodes_http_et_redirections_settings
from app.services.passive.both.cors_cross_origin.checks import CorsCrossOriginCheckResult, MethodesDataEntry
from app.utils.url_helpers import build_url_with_path


@dataclass(frozen=True)
class MethodesHttpIssue:
    """Issue Méthodes HTTP / redirections typée."""

    kind: str
    message: str


@dataclass(frozen=True)
class MethodesHttpCheckResult:
    """Résultat des vérifications Méthodes HTTP et redirections."""

    issues: tuple[MethodesHttpIssue, ...]
    fetch_ok: bool = True
    scan_type: str = "frontend"  # Pour ajuster la sévérité (ex. dangerous_methods: frontend→low, backend→info)


def _is_form_sensitive_url(url: str, form_paths: tuple[str, ...]) -> bool:
    """Indique si l'URL correspond à un chemin formulaire sensible."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return any(f and f in path for f in form_paths)


async def _check_trace(
    client: httpx.AsyncClient,
    url: str,
    timeout: float,
    issues: list[MethodesHttpIssue],
) -> None:
    """Envoie TRACE et signale si activé (200 + écho)."""
    try:
        resp = await client.request("TRACE", url, timeout=timeout)
    except Exception:
        return
    if resp.status_code != 200:
        return
    # Vérifier que le corps contient un écho (la requête reflétée)
    body = (resp.text or "").strip()
    if body and ("TRACE" in body or len(body) > 10):
        msg = f"TRACE activé (risque XST) : {url}."
        issues.append(MethodesHttpIssue(kind="trace_enabled", message=msg))


async def _check_head(
    client: httpx.AsyncClient,
    url: str,
    timeout: float,
    issues: list[MethodesHttpIssue],
) -> None:
    """Vérifie que HEAD est supporté ; sinon info (pas un finding critique)."""
    try:
        resp = await client.head(url, timeout=timeout)
    except Exception:
        return
    if resp.status_code >= 400:
        msg = f"HEAD non supporté (HTTP {resp.status_code}) : {url}."
        issues.append(MethodesHttpIssue(kind="head_unsupported", message=msg))


def _collect_from_methodes_data(
    methodes_data: tuple[MethodesDataEntry, ...],
    issues: list[MethodesHttpIssue],
) -> None:
    """Produit les findings PUT/DELETE/PATCH depuis les données CORS."""
    for url, allow, acam in methodes_data:
        methods = allow | acam
        dangerous = methods & {"PUT", "DELETE", "PATCH"}
        if not dangerous:
            continue
        # API ou endpoint sensible : émettre
        msg = f"Méthodes potentiellement dangereuses exposées ({', '.join(sorted(dangerous))}) : {url}."
        issues.append(MethodesHttpIssue(kind="dangerous_methods", message=msg))


def _collect_redirect_issues(
    response: httpx.Response | None,
    redirect_chain_max: int,
    form_paths: tuple[str, ...],
    check_chain: bool,
    check_301_302: bool,
    page_url: str,
    issues: list[MethodesHttpIssue],
) -> None:
    """Analyse response.history pour chaîne excessive et 301/302 sur formulaire."""
    if response is None:
        return
    history = getattr(response, "history", None) or []
    if check_chain and len(history) > redirect_chain_max:
        msg = f"Chaîne de redirection excessive ({len(history)} > {redirect_chain_max}) : {page_url}."
        issues.append(MethodesHttpIssue(kind="redirect_chain_excessive", message=msg))
    if not check_301_302 or not form_paths:
        return
    final_url = str(getattr(response, "url", page_url) or page_url)
    if not _is_form_sensitive_url(final_url, form_paths):
        return
    for r in history:
        if r.status_code in (301, 302):
            msg = f"Redirection 301/302 sur formulaire sensible (préférer 307/308 pour préserver POST) : {page_url}."
            issues.append(MethodesHttpIssue(kind="redirect_301_302_form", message=msg))
            break


async def run_methodes_http_checks(
    response: httpx.Response | None,
    url: str,
    client: httpx.AsyncClient,
    *,
    cors_result: CorsCrossOriginCheckResult | None = None,
    scan_type: str = "frontend",
) -> MethodesHttpCheckResult:
    """Exécute les vérifications Méthodes HTTP et redirections.

    Réutilise methodes_data du résultat CORS (Allow, ACAM). Effectue TRACE,
    HEAD, et analyse les redirections depuis response.history.

    Args:
        response: Réponse HTTP de la page (fetch initial avec follow_redirects).
        url: URL de la page.
        client: Client HTTPX partagé.
        cors_result: Résultat CORS contenant methodes_data (Allow/ACAM par URL).
        scan_type: "frontend" ou "backend".

    Returns:
        MethodesHttpCheckResult: Issues collectées.
    """
    issues: list[MethodesHttpIssue] = []
    settings = get_methodes_http_et_redirections_settings()
    cors_settings = get_cors_cross_origin_settings()

    # 1. Allow/ACAM + PUT/DELETE/PATCH depuis CORS
    methodes_data = cors_result.methodes_data if cors_result else ()
    _collect_from_methodes_data(methodes_data, issues)

    # 2. TRACE (page + chemins sensibles, limité)
    if settings.check_trace and response is not None:
        base = url.rstrip("/") or url
        urls_trace = [url]
        for path in cors_settings.sensitive_paths[: settings.trace_max_urls - 1]:
            if not path.strip():
                continue
            derived = build_url_with_path(base, path)
            if derived not in urls_trace:
                urls_trace.append(derived)
        for u in urls_trace[: settings.trace_max_urls]:
            await _check_trace(client, u, settings.trace_timeout, issues)

    # 3. HEAD (page uniquement)
    if settings.check_head:
        await _check_head(client, url, settings.trace_timeout, issues)

    # 4. Redirections
    _collect_redirect_issues(
        response,
        settings.redirect_chain_max,
        settings.form_sensitive_paths,
        settings.check_redirect_chain,
        settings.check_redirect_301_302,
        url,
        issues,
    )

    return MethodesHttpCheckResult(issues=tuple(issues), fetch_ok=True, scan_type=scan_type)
