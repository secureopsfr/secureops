"""Noyau commun du scan: contexte, étapes et payload final."""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.catalogue.category_summaries import build_category_summaries
from app.models.scan_result import ScanResult
from app.services.passive.cache import checks as cache_checks
from app.services.passive.cookies import check_cookies_from_response
from app.services.passive.cors_cross_origin import run_cors_cross_origin_checks
from app.services.passive.directory_listing import run_directory_listing_checks
from app.services.passive.exposed_files import run_exposed_files_checks
from app.services.passive.information_disclosure import check_information_disclosure_from_response
from app.services.passive.integrity import check_integrity_from_response
from app.services.passive.normalization import normalize_results
from app.services.passive.robots_txt import run_robots_txt_checks
from app.services.passive.security_headers import check_security_headers_from_response
from app.services.passive.sitemap import run_sitemap_checks
from app.services.passive.tech_fingerprinting import check_tech_fingerprinting_from_response
from app.services.passive.tls import run_tls_checks
from app.services.passive.tls.posture import compute_tls_posture
from app.services.scoring import compute_score


@dataclass(frozen=True)
class FindingsBundle:
    """Résultat intermédiaire consolidé d'un scan ou d'une page.

    Partagé entre le scan single-URL (build_result_payload) et le scan
    multi-URL (_run_page, _build_error_page_result dans multi_scan_orchestrator).
    Évite de dupliquer le bloc normalize -> score -> summaries -> count.

    Attributes:
        findings: Tuple de findings normalisés.
        score: Score de sécurité (0-100).
        category_summaries: Résumés par catégorie avec checks_count.
        total_tests_count: Nombre total de tests effectués.
    """

    findings: tuple
    score: int
    category_summaries: list
    total_tests_count: int


def build_findings_bundle(results: dict[str, object]) -> FindingsBundle:
    """Calcule findings, score et résumés depuis un dict de résultats de checks.

    Source unique pour la logique normalize -> score -> tls_posture ->
    build_category_summaries -> total_tests_count. Tout changement de scoring
    ou de catégorisation n'est à faire qu'ici.

    Args:
        results: Dict {step_name: check_result} issu d'un scan (ex. "tls",
            "headers", "cache"...). Peut contenir un sous-ensemble de steps.

    Returns:
        FindingsBundle prêt à être converti en payload ou PageScanResult.
    """
    findings = normalize_results(results)
    findings_tuple = tuple(findings)
    score = compute_score(findings_tuple)
    tls_result = results.get("tls")
    tls_posture = compute_tls_posture(tls_result) if tls_result else None
    tls_version = getattr(tls_result, "tls_version", None)
    category_summaries = build_category_summaries(
        findings_tuple,
        tls_posture=tls_posture,
        tls_version=tls_version,
    )
    total_tests_count = sum(s.get("checks_count", 0) for s in category_summaries)
    return FindingsBundle(
        findings=findings_tuple,
        score=score,
        category_summaries=category_summaries,
        total_tests_count=total_tests_count,
    )


@dataclass
class ScanContext:
    """Contexte partagé entre les étapes de scan."""

    normalized_url: str
    https_url: str
    client: object
    https_response: object
    results: dict[str, object] = field(default_factory=dict)


# Étapes de scan partagées entre SSE et endpoint interne.
SCAN_STEPS: list[tuple[str, Callable]] = [
    (
        "tls",
        lambda ctx: run_tls_checks(
            ctx.normalized_url,
            https_response=ctx.https_response,
            client=ctx.client,
        ),
    ),
    ("headers", lambda ctx: check_security_headers_from_response(ctx.https_response)),
    (
        "cache",
        lambda ctx: cache_checks.check_cache_from_response(
            ctx.https_response,
            ctx.https_url,
            ctx.client,
        ),
    ),
    ("cookies", lambda ctx: check_cookies_from_response(ctx.https_response, is_https=ctx.results["tls"].https_enabled)),
    ("exposed_files", lambda ctx: run_exposed_files_checks(ctx.https_url, client=ctx.client)),
    ("directory_listing", lambda ctx: run_directory_listing_checks(ctx.https_url, client=ctx.client)),
    ("robots_txt", lambda ctx: run_robots_txt_checks(ctx.https_url, client=ctx.client)),
    (
        "sitemap",
        lambda ctx: run_sitemap_checks(
            ctx.https_url,
            robots_txt_result=ctx.results.get("robots_txt"),
            client=ctx.client,
        ),
    ),
    ("tech_fingerprinting", lambda ctx: check_tech_fingerprinting_from_response(ctx.https_response)),
    ("information_disclosure", lambda ctx: check_information_disclosure_from_response(ctx.https_response)),
    ("integrity", lambda ctx: check_integrity_from_response(ctx.https_response, ctx.https_url)),
    (
        "cors_cross_origin",
        lambda ctx: run_cors_cross_origin_checks(
            ctx.https_response,
            ctx.https_url,
            ctx.client,
        ),
    ),
]


def build_result_payload(
    url: str,
    results: dict[str, object],
    start_time: float | None = None,
    *,
    scan_type: str = "frontend",
) -> dict:
    """Construit le payload normalisé final du scan single-URL."""
    bundle = build_findings_bundle(results)
    duration = (time.monotonic() - start_time) if start_time is not None else 0.0
    timestamp = datetime.now(timezone.utc).isoformat()
    scan_result = ScanResult(
        url=url,
        timestamp=timestamp,
        duration=duration,
        score=bundle.score,
        findings=bundle.findings,
    )
    payload = scan_result.to_dict()
    payload["category_summaries"] = bundle.category_summaries
    payload["total_tests_count"] = bundle.total_tests_count
    payload["scan_type"] = scan_type
    payload["status"] = "success"
    return payload
