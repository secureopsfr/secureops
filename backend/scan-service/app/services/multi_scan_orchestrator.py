"""Orchestrateur du scan multi-URL sur un même domaine.

Exécute les checks en deux phases :
- Phase 1 (domaine) : TLS, robots.txt, sitemap, exposed_files, directory_listing, CORS
  base — exécutés une seule fois, concurremment, pour tout le domaine.
- Phase 2 (pages)  : headers, cookies, cache, tech_fingerprinting, information_disclosure,
  integrity, CORS page — exécutés pour chaque URL, avec concurrence limitée par semaphore.

Les résultats de la phase domaine sont réutilisés dans chaque rapport de page.
Le cache d'assets CSS/JS est partagé entre toutes les pages pour éviter les requêtes dupliquées.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import httpx

from app.catalogue.category_summaries import build_category_summaries
from app.config_loader import get_multi_scan_settings, get_ssrf_settings
from app.models.multi_scan import MultiScanResult, PageScanResult
from app.services.cache import checks as cache_checks
from app.services.cookies import check_cookies_from_response
from app.services.cors_cross_origin.checks import run_cors_domain_checks, run_cors_page_checks
from app.services.directory_listing import run_directory_listing_checks
from app.services.exposed_files import run_exposed_files_checks
from app.services.information_disclosure import check_information_disclosure_from_response
from app.services.integrity import check_integrity_from_response
from app.services.normalization import normalize_results
from app.services.robots_txt import run_robots_txt_checks
from app.services.scoring import compute_score
from app.services.security_headers import check_security_headers_from_response
from app.services.sitemap import run_sitemap_checks
from app.services.tech_fingerprinting import check_tech_fingerprinting_from_response
from app.services.tls import run_tls_checks
from app.services.tls.posture import compute_tls_posture
from app.utils.http_fetch import (
    get_scan_http_request_count,
    get_scan_http_requests_by_category,
    get_with_client_or_error,
    http_request_category,
    scan_client,
)
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url, registered_domain
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)

OnProgress = Callable[[str, str], Awaitable[None]] | None


async def _emit_progress(on_progress: OnProgress, step: str, message: str) -> None:
    """Émet un événement de progression si callback fourni."""
    if on_progress:
        await on_progress(step, message)


async def run_multi_scan(
    urls: list[str],
    on_progress: OnProgress = None,
) -> MultiScanResult:
    """Exécute le scan multi-URL et retourne le résultat agrégé.

    Args:
        urls: Liste d'URLs à scanner (même domaine, déjà validées SSRF).
        on_progress: Callback (step, message) appelé à chaque étape de progression.

    Returns:
        MultiScanResult: Résultat agrégé avec score global et résultats par page.
    """
    start = time.monotonic()
    settings = get_multi_scan_settings()

    # Normaliser et dériver la base URL depuis la première URL.
    normalized_first = validate_and_normalize_url(urls[0])
    base_url = get_scan_base_url(normalized_first)

    async with scan_client() as client:
        try:
            # ── Phase 1 : domain checks (concurrent) ─────────────────────────────
            domain_results: dict[str, Any] = {}
            await _run_domain_phase(
                base_url,
                client,
                domain_results,
                on_progress,
            )

            # ── Phase 2 : page checks (concurrent, limité par semaphore) ─────────
            assets_cache: dict[str, str | None] = {}
            semaphore = asyncio.Semaphore(settings.concurrent_pages)

            page_tasks = [
                _run_page_with_semaphore(
                    url=url,
                    client=client,
                    domain_results=domain_results,
                    assets_cache=assets_cache,
                    semaphore=semaphore,
                    page_timeout=settings.page_timeout,
                    on_progress=on_progress,
                    page_index=i,
                    total_pages=len(urls),
                )
                for i, url in enumerate(urls)
            ]
            raw_results = await asyncio.gather(*page_tasks)
            page_results = list(raw_results)
        finally:
            logger.info(
                "multi-scan: http_requests_count=%s http_requests_by_category=%s base_url=%s urls=%s",
                get_scan_http_request_count(client),
                get_scan_http_requests_by_category(client),
                base_url,
                len(urls),
            )

    # ── Phase 3 : merge & score global ───────────────────────────────────────
    duration = time.monotonic() - start
    timestamp = datetime.now(timezone.utc).isoformat()
    score_global = _compute_global_score(page_results)

    if on_progress:
        await on_progress("multi_scan_done", f"Scan multi-URL terminé. Score global : {score_global}/100.")

    return MultiScanResult(
        base_url=base_url,
        urls=urls,
        score_global=score_global,
        page_results=page_results,
        timestamp=timestamp,
        duration=duration,
    )


async def _run_domain_phase(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    """Exécute les checks domaine en parallèle et peuple domain_results.

    robots_txt → sitemap sont chaînés (sitemap lit le résultat robots).
    TLS, exposed_files, directory_listing et CORS base sont indépendants.
    """
    await asyncio.gather(
        _run_domain_tls(
            base_url,
            client,
            domain_results,
            on_progress,
        ),
        _run_domain_robots_then_sitemap(
            base_url,
            client,
            domain_results,
            on_progress,
        ),
        _run_domain_exposed_files(
            base_url,
            client,
            domain_results,
            on_progress,
        ),
        _run_domain_directory_listing(
            base_url,
            client,
            domain_results,
            on_progress,
        ),
        _run_domain_cors(
            base_url,
            client,
            domain_results,
            on_progress,
        ),
    )

    await _emit_progress(on_progress, "domain_checks_done", "Checks domaine terminés.")


async def _run_domain_robots_then_sitemap(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    await _emit_progress(on_progress, "domain_robots_check", "Vérification robots.txt…")
    with http_request_category("robots_txt"):
        domain_results["robots_txt"] = await run_robots_txt_checks(base_url, client=client)
    await _emit_progress(on_progress, "domain_sitemap_check", "Vérification sitemap…")
    with http_request_category("sitemap"):
        domain_results["sitemap"] = await run_sitemap_checks(
            base_url,
            robots_txt_result=domain_results["robots_txt"],
            client=client,
        )


async def _run_domain_tls(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    await _emit_progress(on_progress, "domain_tls_check", "Vérification TLS/HTTPS…")
    normalized = validate_and_normalize_url(base_url)
    with http_request_category("tls"):
        fetch_result = await get_with_client_or_error(client, base_url, follow_redirects=True)
        https_response = fetch_result.response if fetch_result.success else None
        domain_results["tls"] = await run_tls_checks(
            normalized,
            https_response=https_response,
            client=client,
        )


async def _run_domain_exposed_files(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    await _emit_progress(
        on_progress,
        "domain_exposed_files_check",
        "Vérification fichiers exposés…",
    )
    with http_request_category("exposed_files"):
        domain_results["exposed_files"] = await run_exposed_files_checks(base_url, client=client)


async def _run_domain_directory_listing(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    await _emit_progress(
        on_progress,
        "domain_directory_listing_check",
        "Vérification directory listing…",
    )
    with http_request_category("directory_listing"):
        domain_results["directory_listing"] = await run_directory_listing_checks(base_url, client=client)


async def _run_domain_cors(
    base_url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    on_progress: OnProgress,
) -> None:
    await _emit_progress(on_progress, "domain_cors_check", "Vérification CORS (domaine)…")
    with http_request_category("cors_cross_origin"):
        domain_results["cors_domain"] = await run_cors_domain_checks(base_url, client=client)


async def _run_page_with_semaphore(
    *,
    url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    assets_cache: dict[str, str | None],
    semaphore: asyncio.Semaphore,
    page_timeout: float,
    on_progress: OnProgress,
    page_index: int,
    total_pages: int,
) -> PageScanResult:
    """Acquiert le sémaphore puis délègue au scan de page."""
    async with semaphore:
        return await _run_page(
            url=url,
            client=client,
            domain_results=domain_results,
            assets_cache=assets_cache,
            page_timeout=page_timeout,
            on_progress=on_progress,
            page_index=page_index,
            total_pages=total_pages,
        )


async def _run_page(
    *,
    url: str,
    client: httpx.AsyncClient,
    domain_results: dict[str, Any],
    assets_cache: dict[str, str | None],
    page_timeout: float,
    on_progress: OnProgress,
    page_index: int,
    total_pages: int,
) -> PageScanResult:
    """Exécute les checks page pour une URL et retourne le PageScanResult.

    Une page inaccessible retourne un résultat partiel (findings domaine conservés,
    score 0, champ error renseigné) sans faire échouer le scan global.
    """
    if on_progress:
        await on_progress(
            "page_scan_started",
            f"Analyse de {url} ({page_index + 1}/{total_pages})…",
        )

    try:
        with http_request_category("initial_fetch"):
            response = await asyncio.wait_for(
                client.get(url, follow_redirects=True),
                timeout=page_timeout,
            )
    except Exception as exc:
        logger.warning("multi_scan: page inaccessible url=%s err=%s", url, exc)
        if on_progress:
            await on_progress("page_scan_error", f"Page inaccessible : {url}")
        return _build_error_page_result(url, str(exc), domain_results)

    page_results: dict[str, Any] = {}
    tls_result = domain_results.get("tls")
    is_https = getattr(tls_result, "https_enabled", True)

    # Checks page (tous passifs sauf cache qui fait des HEAD/GET sur assets).
    page_results["headers"] = check_security_headers_from_response(response)
    page_results["cookies"] = check_cookies_from_response(response, is_https=is_https)
    page_results["tech_fingerprinting"] = check_tech_fingerprinting_from_response(response)
    page_results["information_disclosure"] = check_information_disclosure_from_response(response)
    page_results["integrity"] = check_integrity_from_response(response, url)
    with http_request_category("cache"):
        page_results["cache"] = await cache_checks.check_cache_from_response(response, url, client, assets_cache=assets_cache)
    with http_request_category("cors_cross_origin"):
        page_results["cors_cross_origin"] = await run_cors_page_checks(
            response,
            url,
            client,
            domain_result=domain_results.get("cors_domain"),
        )

    # Résultats finaux = domaine + page (sans cors_domain déjà fusionné dans cors_cross_origin).
    merged: dict[str, Any] = {k: v for k, v in domain_results.items() if k != "cors_domain"}
    merged.update(page_results)

    findings = normalize_results(merged)
    findings_tuple = tuple(findings)
    score = compute_score(findings_tuple)

    tls_posture = compute_tls_posture(tls_result) if tls_result else None
    tls_version = getattr(tls_result, "tls_version", None)
    category_summaries = build_category_summaries(findings_tuple, tls_posture=tls_posture, tls_version=tls_version)
    total_tests_count = sum(s.get("checks_count", 0) for s in category_summaries)

    if on_progress:
        await on_progress("page_scan_done", f"Page analysée : {url}")

    return PageScanResult(
        url=url,
        score=score,
        findings=[f.to_dict() for f in findings_tuple],
        category_summaries=category_summaries,
        total_tests_count=total_tests_count,
    )


def _build_error_page_result(
    url: str,
    error_message: str,
    domain_results: dict[str, Any],
) -> PageScanResult:
    """Construit un résultat partiel pour une page inaccessible.

    Les findings domaine (TLS, exposed_files, etc.) sont inclus car ils
    s'appliquent à toutes les pages du domaine même si cette page est down.
    """
    domain_only: dict[str, Any] = {k: v for k, v in domain_results.items() if k != "cors_domain"}
    findings = normalize_results(domain_only)
    findings_tuple = tuple(findings)
    score = compute_score(findings_tuple)

    tls_result = domain_results.get("tls")
    tls_posture = compute_tls_posture(tls_result) if tls_result else None
    tls_version = getattr(tls_result, "tls_version", None)
    category_summaries = build_category_summaries(findings_tuple, tls_posture=tls_posture, tls_version=tls_version)

    return PageScanResult(
        url=url,
        score=score,
        findings=[f.to_dict() for f in findings_tuple],
        category_summaries=category_summaries,
        error=error_message,
    )


def _compute_global_score(page_results: list[PageScanResult]) -> int:
    """Calcule le score global (moyenne pondérée).

    Les pages avec erreur contribuent avec un poids 0.5 (signal dégradé,
    pas ignoré) et un score de 0.
    """
    if not page_results:
        return 0
    weights = [0.5 if r.error else 1.0 for r in page_results]
    scores = [0 if r.error else r.score for r in page_results]
    total_weight = sum(weights)
    if total_weight == 0:
        return 0
    return int(sum(s * w for s, w in zip(scores, weights)) / total_weight)


async def validate_multi_scan_urls(urls: list[str]) -> list[str]:
    """Valide et normalise les URLs, vérifie SSRF sur le domaine de base.

    Args:
        urls: URLs brutes à valider.

    Returns:
        list[str]: URLs normalisées (peut différer des entrées).

    Raises:
        URLValidationError: Si une URL est invalide.
        SSRFError: Si l'hôte est interdit (SSRF check).
        ValueError: Si les URLs appartiennent à des domaines enregistrés différents.
    """
    from app.utils.url_validator import URLValidationError  # noqa: F401

    normalized: list[str] = []
    for url in urls:
        n = validate_and_normalize_url(url)
        normalized.append(n)

    # Vérification domaine enregistré unique (eTLD+1 via tldextract).
    # community.finary.com et finary.com → même domaine "finary.com" → OK.
    reg_domains = {registered_domain(get_scan_base_url(u)) for u in normalized}
    reg_domains.discard("")
    if len(reg_domains) > 1:
        raise ValueError(f"Toutes les URLs doivent appartenir au même domaine enregistré. " f"Domaines détectés : {', '.join(sorted(reg_domains))}")

    # SSRF check une seule fois sur le domaine commun.
    await check_ssrf(normalized[0], timeout=get_ssrf_settings().dns_timeout)

    return normalized
