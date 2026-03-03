"""Normaliseurs : conversion des résultats de checks en list[Finding].

Chaque fonction prend un résultat brut et retourne une liste de Finding normalisés.
Sévérité en minuscules. Règles d'upgrade : .git/config, .env exposés = critical.
"""

import re
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
from app.services.sitemap.checks import SitemapCheckResult
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


def _extract_days_until_expiry(msg: str) -> int | None:
    """Extrait le nombre de jours avant expiration depuis un message (ex. "dans 14 jour(s)").

    Args:
        msg: Message contenant potentiellement "dans X jour(s)" ou "in X days".

    Returns:
        int | None: Nombre de jours ou None si non trouvé.
    """
    m = re.search(r"(?:dans|in)\s+(\d+)\s+(?:jour|day)", msg, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _tls_msg_to_finding(msg: str) -> tuple[str, str, str]:
    """Mappe un message TLS vers (slug, title, severity).

    Args:
        msg: Message du finding brut.

    Returns:
        tuple[str, str, str]: (slug, title, severity).
    """
    msg_l = msg.lower()
    if "redirection" in msg_l or "redirect" in msg_l:
        return ("tls-no-redirect", "Pas de redirection HTTP→HTTPS", "high")
    if "expiré" in msg_l or "expired" in msg_l:
        return ("tls-cert-expired", "Certificat expiré", "critical")
    if "auto-signé" in msg_l or "self_signed" in msg_l:
        return ("tls-cert-self-signed", "Certificat auto-signé", "high")
    if "pas encore valide" in msg_l or "notBefore" in msg_l:
        return ("tls-cert-not-yet-valid", "Certificat pas encore valide", "medium")
    if "expire bientôt" in msg_l or "expires soon" in msg_l:
        # Gravité selon le délai : 15-29 jours → low, 0-14 jours → medium
        days = _extract_days_until_expiry(msg)
        severity = "low" if days is not None and days >= 15 else "medium"
        return ("tls-cert-expires-soon", "Certificat expire bientôt", severity)
    if "chaîne" in msg_l and ("incomplète" in msg_l or "invalide" in msg_l):
        return ("tls-chain-incomplete", "Chaîne de certificats incomplète", "medium")
    if "TLS" in msg and ("1.0" in msg or "1.1" in msg):
        return ("tls-versions-obsolete", "Versions TLS obsolètes", "medium")
    if "connexion" in msg_l or "timeout" in msg_l:
        return ("tls-connection-failed", "Connexion HTTPS impossible", "high")
    return ("tls-connection-failed", "Problème TLS", "medium")


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
        slug, title, severity = _tls_msg_to_finding(msg)
        findings.append(_finding(slug, "tls", title, severity, msg))
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
    headers_config = get_security_headers_settings()
    header_to_slug = {cfg.name: cfg.slug for cfg in headers_config}
    header_to_severity = {cfg.name: cfg.severity for cfg in headers_config}
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
        elif "report-uri" in msg and "report-to" in msg and "sans" in msg:
            findings.append(
                _finding(
                    "headers-csp-no-report-uri",
                    "headers",
                    "CSP sans report-uri ni report-to",
                    "low",
                    msg,
                )
            )
        elif "unsafe-inline" in msg or "unsafe-eval" in msg:
            findings.append(
                _finding(
                    "headers-csp-unsafe-directives",
                    "headers",
                    "CSP avec directives unsafe",
                    "low",
                    msg,
                )
            )
        else:
            for h in sorted(header_to_slug, key=len, reverse=True):
                if h in msg and h in result.headers_missing:
                    slug = header_to_slug[h]
                    severity = header_to_severity.get(h, "medium")
                    findings.append(_finding(slug, "headers", f"{h} absent", severity, msg))
                    break
            else:
                findings.append(_finding("headers-connection-failed", "headers", "En-tête manquant", "medium", msg))
    return findings


def _cookie_msg_to_finding(msg: str) -> tuple[str, str, str]:
    """Mappe un message cookie vers (slug, title, severity)."""
    if "Cookie de session" in msg and "HttpOnly + Secure + SameSite=Strict" in msg:
        return ("cookies-session-incomplete", "Cookie de session sans triple protection", "high")
    if "sans préfixe __Host-" in msg or "sans préfixe __Secure-" in msg:
        return ("cookies-no-host-secure-prefix", "Cookie sensible sans préfixe __Host-/__Secure-", "info")
    if "sans Partitioned" in msg:
        return ("cookies-no-partitioned", "Cookie tiers sans Partitioned (CHIPS)", "low")
    if "Expires/Max-Age > 24h" in msg or "session persistante" in msg:
        return ("cookies-session-expires-long", "Cookie de session avec durée trop longue", "low")
    if "Secure" in msg and "HTTPS" in msg:
        return ("cookies-no-secure", "Cookie sans Secure", "high")
    if "HttpOnly" in msg:
        return ("cookies-no-httponly", "Cookie sans HttpOnly", "medium")
    if "SameSite" in msg and "requiert" in msg:
        return ("cookies-samesite-none-requires-secure", "SameSite=None sans Secure", "high")
    if "SameSite" in msg:
        return ("cookies-no-samesite", "Cookie sans SameSite", "medium")
    return ("cookies-connection-failed", "Problème cookie", "medium")


def _normalize_cookies(result: CookieCheckResult) -> list[Finding]:
    """Convertit CookieCheckResult en list[Finding]."""
    if not result.fetch_ok:
        return [
            _finding(
                "cookies-connection-failed",
                "cookies",
                "Cookies inaccessibles",
                "high",
                MSG_COOKIES_UNAVAILABLE,
            )
        ]
    findings: list[Finding] = []
    for msg in result.findings:
        slug, title, severity = _cookie_msg_to_finding(msg)
        findings.append(_finding(slug, "cookies", title, severity, msg))
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


def _normalize_path_check_result(
    result: PathCheckResult,
    category: str,
    title_fn: Callable[[object], str],
    severity_fn: Callable[[object], str],
) -> list[Finding]:
    """Convertit PathCheckResult en list[Finding] (exposed_files ou directory_listing).

    Args:
        result: Résultat du path check.
        category: Catégorie (exposed_files, directory_listing).
        title_fn: pf -> titre du finding.
        severity_fn: pf -> sévérité (lowercase).
    """
    findings: list[Finding] = []
    for pf in result.exposed:
        slug = _path_to_slug(pf.path, category)
        title = title_fn(pf)
        severity = severity_fn(pf)
        findings.append(_finding(slug, category, title, severity, pf.message))
    return findings


def _normalize_exposed_files(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (exposed_files) en list[Finding]."""
    return _normalize_path_check_result(
        result,
        "exposed_files",
        title_fn=lambda pf: f"Fichier exposé : {pf.path}",
        severity_fn=lambda pf: _path_severity(pf.path, pf.severity),
    )


def _normalize_directory_listing(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (directory_listing) en list[Finding]."""
    return _normalize_path_check_result(
        result,
        "directory_listing",
        title_fn=lambda pf: f"Directory listing : {pf.path}",
        severity_fn=lambda pf: pf.severity.lower(),
    )


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
    if result.crawl_delay is not None:
        ev = f"Crawl-delay: {result.crawl_delay}s (directive non standard, certains moteurs l'ignorent)."
        findings.append(_finding("robots_txt-crawl-delay", "robots_txt", "Crawl-delay détecté", "info", ev))
    return findings


def _normalize_sitemap(result: SitemapCheckResult) -> list[Finding]:
    """Convertit SitemapCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.sitemap_found:
        if result.fetch_ok:
            findings.append(
                _finding(
                    "sitemap-not-found",
                    "sitemap",
                    "Sitemap non trouvé",
                    "info",
                    "Aucun sitemap trouvé (ni dans robots.txt, ni à /sitemap.xml). Recommandation : créer et déclarer un sitemap.",
                )
            )
        return findings
    if result.sitemap_undeclared:
        findings.append(
            _finding(
                "sitemap-undeclared",
                "sitemap",
                "Sitemap présent mais non déclaré dans robots.txt",
                "info",
                "Sitemap trouvé à /sitemap.xml mais absent de robots.txt. Recommandation : ajouter Sitemap: dans robots.txt.",
            )
        )
    for su in result.sensitive_urls:
        ev = f"URL sensible dans sitemap : {su.url} (motif : {su.pattern})."
        findings.append(
            _finding(
                "sitemap-sensitive-url",
                "sitemap",
                f"URL sensible exposée dans sitemap : {su.path}",
                su.severity.lower(),
                ev,
            )
        )
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
    sitemap: SitemapCheckResult
    tech_fingerprinting: TechFingerprintingCheckResult


_NORMALIZERS: list[tuple[str, Callable[[object], list[Finding]]]] = [
    ("tls", _normalize_tls),
    ("headers", _normalize_headers),
    ("cookies", _normalize_cookies),
    ("exposed_files", _normalize_exposed_files),
    ("directory_listing", _normalize_directory_listing),
    ("robots_txt", _normalize_robots_txt),
    ("sitemap", _normalize_sitemap),
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
