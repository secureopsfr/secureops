"""Normaliseurs : conversion des résultats de checks en list[Finding].

Chaque fonction prend un résultat brut et retourne une liste de Finding normalisés.
Sévérité en minuscules. Règles d'upgrade : .git/config, .env exposés = critical.
"""

from app.catalogue.recommendations import get_recommendation, get_references
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
                "HTTPS non activé (connexion refusée ou timeout).",
            )
        )
        return findings
    if not result.https_enabled:
        findings.append(_finding("tls-https-disabled", "tls", "HTTPS non activé", "critical", "Connexion refusée ou timeout."))
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
                "Impossible de récupérer les en-têtes (connexion refusée ou timeout).",
            )
        )
        return findings
    header_to_slug: dict[str, str] = {
        "Content-Security-Policy": "headers-csp-absent",
        "Strict-Transport-Security": "headers-hsts-absent",
        "X-Frame-Options": "headers-xfo-absent",
        "X-Content-Type-Options": "headers-xcto-absent",
        "Referrer-Policy": "headers-referrer-absent",
        "Permissions-Policy": "headers-permissions-absent",
    }
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
                "Impossible d'analyser les cookies (connexion refusée ou timeout).",
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
    """Applique upgrade : .git/config et .env = critical."""
    path_lower = path.lower()
    if "/.git/config" in path_lower or path_lower.endswith(".git/config"):
        return "critical"
    if "/.env" in path_lower or path_lower.endswith(".env"):
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
                "Impossible de récupérer robots.txt (connexion refusée ou timeout).",
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
                "Impossible d'analyser les en-têtes (connexion refusée ou timeout).",
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


def normalize_results(results: dict[str, object]) -> list[Finding]:
    """Convertit tous les résultats de checks en liste de Finding normalisés.

    Args:
        results: Dict clé → résultat (tls, headers, cookies, exposed_files, directory_listing, robots_txt, tech_fingerprinting).

    Returns:
        list[Finding]: Liste de tous les findings normalisés.
    """
    all_findings: list[Finding] = []
    if "tls" in results and results["tls"] is not None:
        all_findings.extend(_normalize_tls(results["tls"]))
    if "headers" in results and results["headers"] is not None:
        all_findings.extend(_normalize_headers(results["headers"]))
    if "cookies" in results and results["cookies"] is not None:
        all_findings.extend(_normalize_cookies(results["cookies"]))
    if "exposed_files" in results and results["exposed_files"] is not None:
        all_findings.extend(_normalize_exposed_files(results["exposed_files"]))
    if "directory_listing" in results and results["directory_listing"] is not None:
        all_findings.extend(_normalize_directory_listing(results["directory_listing"]))
    if "robots_txt" in results and results["robots_txt"] is not None:
        all_findings.extend(_normalize_robots_txt(results["robots_txt"]))
    if "tech_fingerprinting" in results and results["tech_fingerprinting"] is not None:
        all_findings.extend(_normalize_tech_fingerprinting(results["tech_fingerprinting"]))
    return all_findings
