"""Dispatcher de normalisation : délègue à chaque module de check.

Chaque check possède son propre normalizer.py avec une fonction normalize(result).
Ce fichier orchestre uniquement l'appel dans l'ordre canonique des catégories.
Ajouter une nouvelle catégorie = créer son normalizer.py et l'inscrire ici.
"""

from typing import TypedDict

from app.models.finding import Finding
from app.services.passive.cache.checks import CacheCheckResult
from app.services.passive.cache.normalizer import normalize as normalize_cache
from app.services.passive.cookies.checks import CookieCheckResult
from app.services.passive.cookies.normalizer import normalize as normalize_cookies
from app.services.passive.cors_cross_origin.checks import CorsCrossOriginCheckResult
from app.services.passive.cors_cross_origin.normalizer import normalize as normalize_cors
from app.services.passive.information_disclosure.checks import InformationDisclosureCheckResult
from app.services.passive.information_disclosure.normalizer import normalize as normalize_info_disclosure
from app.services.passive.integrity.checks import IntegrityCheckResult
from app.services.passive.integrity.normalizer import normalize as normalize_integrity
from app.services.passive.path_checks.core import PathCheckResult
from app.services.passive.path_checks.normalizer import normalize_directory_listing, normalize_exposed_files
from app.services.passive.robots_txt.checks import RobotsTxtCheckResult
from app.services.passive.robots_txt.normalizer import normalize as normalize_robots_txt
from app.services.passive.security_headers.checks import SecurityHeadersCheckResult
from app.services.passive.security_headers.normalizer import normalize as normalize_headers
from app.services.passive.sitemap.checks import SitemapCheckResult
from app.services.passive.sitemap.normalizer import normalize as normalize_sitemap
from app.services.passive.tech_fingerprinting.checks import TechFingerprintingCheckResult
from app.services.passive.tech_fingerprinting.normalizer import normalize as normalize_tech
from app.services.passive.tls.checks import TlsCheckResult
from app.services.passive.tls.normalizer import normalize as normalize_tls


class ScanResultsDict(TypedDict, total=False):
    """Structure des résultats de checks passés à normalize_results."""

    tls: TlsCheckResult
    headers: SecurityHeadersCheckResult
    cookies: CookieCheckResult
    exposed_files: PathCheckResult
    directory_listing: PathCheckResult
    robots_txt: RobotsTxtCheckResult
    sitemap: SitemapCheckResult
    tech_fingerprinting: TechFingerprintingCheckResult
    cache: CacheCheckResult
    information_disclosure: InformationDisclosureCheckResult
    cors_cross_origin: CorsCrossOriginCheckResult
    integrity: IntegrityCheckResult


# Ordre canonique des catégories — chaque entrée est (clé_résultat, fonction_normalize).
_NORMALIZERS: list[tuple[str, object]] = [
    ("tls", normalize_tls),
    ("headers", normalize_headers),
    ("cache", normalize_cache),
    ("cookies", normalize_cookies),
    ("exposed_files", normalize_exposed_files),
    ("directory_listing", normalize_directory_listing),
    ("robots_txt", normalize_robots_txt),
    ("sitemap", normalize_sitemap),
    ("tech_fingerprinting", normalize_tech),
    ("information_disclosure", normalize_info_disclosure),
    ("cors_cross_origin", normalize_cors),
    ("integrity", normalize_integrity),
]


def normalize_results(results: ScanResultsDict | dict[str, object]) -> list[Finding]:
    """Convertit tous les résultats de checks en liste de Finding normalisés.

    Args:
        results: Dict clé → résultat (tls, headers, cookies, exposed_files, …).

    Returns:
        list[Finding]: Liste de tous les findings normalisés.
    """
    all_findings: list[Finding] = []
    for key, normalizer_fn in _NORMALIZERS:
        if key in results and results[key] is not None:
            all_findings.extend(normalizer_fn(results[key]))  # type: ignore[arg-type]
    return all_findings
