"""Normaliseurs : conversion des résultats de checks en list[Finding].

Chaque fonction prend un résultat brut et retourne une liste de Finding normalisés.
Sévérité en minuscules. Règles d'upgrade : .git/config, .env exposés = critical.
"""

from typing import Callable, TypedDict

from app.catalogue.recommendations import get_recommendation, get_references
from app.config_loader import get_exposed_files_severity_upgrade, get_security_headers_settings
from app.constants import (
    MSG_COOKIES_UNAVAILABLE,
    MSG_HEADERS_ANALYSIS_UNAVAILABLE,
    MSG_HEADERS_UNAVAILABLE,
    MSG_HTTPS_UNAVAILABLE,
    MSG_ROBOTS_TXT_UNAVAILABLE,
)
from app.models.finding import Finding
from app.services.cookies.checks import CookieCheckResult
from app.services.path_checks.core import PathCheckResult
from app.services.robots_txt.checks import RobotsTxtCheckResult
from app.services.security_headers.checks import SecurityHeadersCheckResult
from app.services.tech_fingerprinting.checks import TechFingerprintingCheckResult
from app.services.tls.checks import TlsCheckResult


def _finding(slug: str, category: str, title: str, severity: str, evidence: str) -> Finding:
    """Crée un Finding avec recommendation et references depuis le catalogue."""
    sev = severity.lower() if severity else "medium"
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=sev,
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
    )


def _normalize_tls(result: TlsCheckResult) -> list[Finding]:
    """Convertit TlsCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "tls-connection-failed",
                "tls",
                "Connexion HTTPS impossible",
                "high",
                MSG_HTTPS_UNAVAILABLE,
            )
        )
        return findings
    if not result.https_enabled:
        findings.append(_finding("tls-https-disabled", "tls", "HTTPS non activé", "critical", MSG_HTTPS_UNAVAILABLE))
        return findings
    for msg in result.findings:
        if "redirection" in msg.lower() or "redirect" in msg.lower():
            findings.append(_finding("tls-no-redirect", "tls", "Pas de redirection HTTP→HTTPS", "high", msg))
        elif "expiré" in msg.lower() or "expired" in msg.lower():
            findings.append(_finding("tls-cert-expired", "tls", "Certificat expiré", "critical", msg))
        elif "auto-signé" in msg.lower() or "self_signed" in msg.lower():
            findings.append(_finding("tls-cert-self-signed", "tls", "Certificat auto-signé", "high", msg))
        elif "pas encore valide" in msg.lower() or "notBefore" in msg.lower():
            findings.append(_finding("tls-cert-not-yet-valid", "tls", "Certificat pas encore valide", "medium", msg))
        elif "TLS" in msg and ("1.0" in msg or "1.1" in msg):
            findings.append(_finding("tls-versions-obsolete", "tls", "Versions TLS obsolètes", "medium", msg))
        elif "connexion" in msg.lower() or "timeout" in msg.lower():
            findings.append(_finding("tls-connection-failed", "tls", "Connexion HTTPS impossible", "high", msg))
        else:
            findings.append(_finding("tls-connection-failed", "tls", "Problème TLS", "medium", msg))
    return findings


def _normalize_headers(result: SecurityHeadersCheckResult) -> list[Finding]:
    """Convertit SecurityHeadersCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "headers-connection-failed",
                "headers",
                "En-têtes inaccessibles",
                "high",
                MSG_HEADERS_UNAVAILABLE,
            )
        )
        return findings
    header_to_slug = {cfg.name: cfg.slug for cfg in get_security_headers_settings()}
    for msg in result.findings:
        if "valeur incorrecte" in msg.lower() or "incorrecte" in msg.lower():
            findings.append(
                _finding(
                    "headers-xcto-wrong-value",
                    "headers",
                    "X-Content-Type-Options valeur incorrecte",
                    "medium",
                    msg,
                )
            )
        else:
            for h in sorted(header_to_slug, key=len, reverse=True):
                if h in msg and h in result.headers_missing:
                    slug = header_to_slug[h]
                    findings.append(_finding(slug, "headers", f"{h} absent", "medium", msg))
                    break
            else:
                findings.append(_finding("headers-connection-failed", "headers", "En-tête manquant", "medium", msg))
    return findings


def _normalize_cookies(result: CookieCheckResult) -> list[Finding]:
    """Convertit CookieCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "cookies-connection-failed",
                "cookies",
                "Cookies inaccessibles",
                "high",
                MSG_COOKIES_UNAVAILABLE,
            )
        )
        return findings
    for msg in result.findings:
        if "Secure" in msg and "HTTPS" in msg:
            findings.append(_finding("cookies-no-secure", "cookies", "Cookie sans Secure", "high", msg))
        elif "HttpOnly" in msg:
            findings.append(_finding("cookies-no-httponly", "cookies", "Cookie sans HttpOnly", "medium", msg))
        elif "SameSite" in msg and "requiert" in msg:
            findings.append(_finding("cookies-samesite-none-requires-secure", "cookies", "SameSite=None sans Secure", "high", msg))
        elif "SameSite" in msg:
            findings.append(_finding("cookies-no-samesite", "cookies", "Cookie sans SameSite", "medium", msg))
        else:
            findings.append(_finding("cookies-connection-failed", "cookies", "Problème cookie", "medium", msg))
    return findings


def _path_to_slug(path: str, category: str) -> str:
    """Retourne le slug pour un chemin exposé."""
    p = path.rstrip("/").lower().replace(".", "-").replace("/", "-").strip("-") or "root"
    return f"{category}-{p}"


def _path_severity(path: str, config_severity: str) -> str:
    """Applique upgrade : chemins dans severity_upgrade (settings.yml) = critical."""
    path_norm = path.rstrip("/") or "/"
    for up in get_exposed_files_severity_upgrade():
        up_norm = up.rstrip("/") or "/"
        if path_norm == up_norm or path_norm.endswith("/" + up_norm.lstrip("/")):
            return "critical"
    return config_severity.lower()


def _normalize_exposed_files(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (exposed_files) en list[Finding]."""
    findings: list[Finding] = []
    for pf in result.exposed:
        slug = _path_to_slug(pf.path, "exposed_files")
        severity = _path_severity(pf.path, pf.severity)
        findings.append(_finding(slug, "exposed_files", f"Fichier exposé : {pf.path}", severity, pf.message))
    return findings


def _normalize_directory_listing(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (directory_listing) en list[Finding]."""
    findings: list[Finding] = []
    for pf in result.exposed:
        slug = _path_to_slug(pf.path, "directory_listing")
        findings.append(_finding(slug, "directory_listing", f"Directory listing : {pf.path}", pf.severity.lower(), pf.message))
    return findings


def _normalize_robots_txt(result: RobotsTxtCheckResult) -> list[Finding]:
    """Convertit RobotsTxtCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "robots_txt-connection-failed",
                "robots_txt",
                "robots.txt inaccessible",
                "high",
                MSG_ROBOTS_TXT_UNAVAILABLE,
            )
        )
        return findings
    for route in result.sensitive_routes:
        ev = f"Disallow: {route.path} (motif : {route.pattern}). Vérifier la protection."
        findings.append(_finding("robots_txt-sensitive-route", "robots_txt", f"Route sensible : {route.path}", route.severity.lower(), ev))
    return findings


def _normalize_tech_fingerprinting(result: TechFingerprintingCheckResult) -> list[Finding]:
    """Convertit TechFingerprintingCheckResult en list[Finding] (severity info)."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "tech_fingerprinting-connection-failed",
                "tech_fingerprinting",
                "En-têtes inaccessibles",
                "info",
                MSG_HEADERS_ANALYSIS_UNAVAILABLE,
            )
        )
        return findings
    for msg in result.findings:
        if "Serveur détecté" in msg:
            findings.append(_finding("tech_fingerprinting-server-detected", "tech_fingerprinting", "Serveur détecté", "info", msg))
        elif "Runtime" in msg:
            findings.append(_finding("tech_fingerprinting-runtime-detected", "tech_fingerprinting", "Runtime détecté", "info", msg))
        elif "Framework/CMS" in msg:
            findings.append(_finding("tech_fingerprinting-framework-detected", "tech_fingerprinting", "Framework/CMS détecté", "info", msg))
        elif "non identifiée" in msg or "masquée" in msg:
            findings.append(_finding("tech_fingerprinting-stack-unknown", "tech_fingerprinting", "Stack non identifiée", "info", msg))
        else:
            findings.append(_finding("tech_fingerprinting-server-detected", "tech_fingerprinting", "Info stack", "info", msg))
    return findings


class ScanResultsDict(TypedDict, total=False):
    """Structure des résultats de checks passés à normalize_results."""

    tls: TlsCheckResult
    headers: SecurityHeadersCheckResult
    cookies: CookieCheckResult
    exposed_files: PathCheckResult
    directory_listing: PathCheckResult
    robots_txt: RobotsTxtCheckResult
    tech_fingerprinting: TechFingerprintingCheckResult


_NORMALIZERS: list[tuple[str, Callable[[object], list[Finding]]]] = [
    ("tls", _normalize_tls),
    ("headers", _normalize_headers),
    ("cookies", _normalize_cookies),
    ("exposed_files", _normalize_exposed_files),
    ("directory_listing", _normalize_directory_listing),
    ("robots_txt", _normalize_robots_txt),
    ("tech_fingerprinting", _normalize_tech_fingerprinting),
]


def normalize_results(results: ScanResultsDict | dict[str, object]) -> list[Finding]:
    """Convertit tous les résultats de checks en liste de Finding normalisés.

    Args:
        results: Dict clé → résultat (tls, headers, cookies, exposed_files, directory_listing, robots_txt, tech_fingerprinting).

    Returns:
        list[Finding]: Liste de tous les findings normalisés.
    """
    all_findings: list[Finding] = []
    for key, normalizer_fn in _NORMALIZERS:
        if key in results and results[key] is not None:
            all_findings.extend(normalizer_fn(results[key]))
    return all_findings
