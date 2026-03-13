"""Normaliseurs : conversion des résultats de checks en list[Finding].

Chaque fonction prend un résultat brut et retourne une liste de Finding normalisés.
Sévérité en minuscules. Règles d'upgrade : .git/config, .env exposés = critical.
"""

import re
from typing import Callable, TypedDict

from app.catalogue.recommendations import get_recommendation, get_references
from app.config_loader import get_cookies_settings, get_exposed_files_severity_upgrade, get_security_headers_settings
from app.constants import (
    MSG_COOKIES_UNAVAILABLE,
    MSG_HEADERS_ANALYSIS_UNAVAILABLE,
    MSG_HEADERS_UNAVAILABLE,
    MSG_HTTPS_UNAVAILABLE,
    MSG_ROBOTS_TXT_UNAVAILABLE,
)
from app.models.finding import Finding
from app.services.passive.cache.checks import CacheCheckResult
from app.services.passive.cookies.checks import CookieCheckResult, CookieInfo
from app.services.passive.cors_cross_origin.checks import CorsCrossOriginCheckResult
from app.services.passive.information_disclosure.checks import InformationDisclosureCheckResult
from app.services.passive.integrity import IntegrityCheckResult
from app.services.passive.path_checks.core import PathCheckResult
from app.services.passive.robots_txt.checks import RobotsTxtCheckResult
from app.services.passive.security_headers.checks import SecurityHeadersCheckResult
from app.services.passive.sitemap.checks import SitemapCheckResult
from app.services.passive.tech_fingerprinting.checks import TechFingerprintingCheckResult
from app.services.passive.tls.checks import TlsCheckResult


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

    if result.http_redirects_to_https is False:
        findings.append(
            _finding(
                "tls-no-redirect",
                "tls",
                "Pas de redirection HTTP→HTTPS",
                "high",
                "Pas de redirection HTTP→HTTPS détectée.",
            )
        )
    if result.certificate_status == "expired":
        findings.append(
            _finding(
                "tls-cert-expired",
                "tls",
                "Certificat expiré",
                "critical",
                "Le certificat présenté par le serveur est expiré.",
            )
        )
    elif result.certificate_status == "self_signed":
        findings.append(
            _finding(
                "tls-cert-self-signed",
                "tls",
                "Certificat auto-signé",
                "high",
                "Le certificat présenté par le serveur est auto-signé.",
            )
        )
    elif result.certificate_status == "not_yet_valid":
        findings.append(
            _finding(
                "tls-cert-not-yet-valid",
                "tls",
                "Certificat pas encore valide",
                "medium",
                "Le certificat présenté par le serveur n'est pas encore valide.",
            )
        )
    elif result.certificate_status == "expires_soon":
        expiry_msg = next((m for m in result.findings if "expire bientôt" in m.lower() or "expires soon" in m.lower()), "")
        days = _extract_days_until_expiry(expiry_msg)
        severity = "low" if days is not None and days >= 15 else "medium"
        findings.append(
            _finding(
                "tls-cert-expires-soon",
                "tls",
                "Certificat expire bientôt",
                severity,
                expiry_msg or "Le certificat approche de son expiration.",
            )
        )
    if result.chain_incomplete or any("chaîne" in m.lower() and "incomplète" in m.lower() for m in result.findings):
        findings.append(
            _finding(
                "tls-chain-incomplete",
                "tls",
                "Chaîne de certificats incomplète",
                "medium",
                "La chaîne de certificats est incomplète (intermédiaires manquants).",
            )
        )
    if result.tls_versions_obsolete:
        versions = ", ".join(result.tls_versions_obsolete)
        findings.append(
            _finding(
                "tls-versions-obsolete",
                "tls",
                "Versions TLS obsolètes",
                "medium",
                f"Versions TLS obsolètes détectées: {versions}.",
            )
        )
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
    for header_name in result.headers_missing:
        slug = header_to_slug.get(header_name, "headers-connection-failed")
        severity = header_to_severity.get(header_name, "medium")
        findings.append(_finding(slug, "headers", f"{header_name} absent", severity, f"{header_name} absent."))

    for msg in result.findings:
        msg_l = msg.lower()
        if "valeur incorrecte" in msg_l or "incorrecte" in msg_l:
            findings.append(_finding("headers-xcto-wrong-value", "headers", "X-Content-Type-Options valeur incorrecte", "medium", msg))
        elif "report-uri" in msg_l and "report-to" in msg_l and "sans" in msg_l:
            findings.append(_finding("headers-csp-no-report-uri", "headers", "CSP sans report-uri ni report-to", "low", msg))
        elif "unsafe-inline" in msg_l or "unsafe-eval" in msg_l:
            findings.append(_finding("headers-csp-unsafe-directives", "headers", "CSP avec directives unsafe", "low", msg))
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


def _normalize_cookie_structured(cookie: CookieInfo, settings) -> list[Finding]:
    """Normalise un cookie à partir des attributs structurés."""
    cookie_findings: list[Finding] = []
    name_lower = cookie.name.lower()
    session_like = any(p in name_lower for p in settings.session_like_names)
    third_party_like = any(p in name_lower for p in settings.third_party_like_names)

    if session_like and not (cookie.httponly and cookie.secure and cookie.samesite == "Strict"):
        return [
            _finding(
                "cookies-session-incomplete",
                "cookies",
                "Cookie de session sans triple protection",
                "high",
                f"Cookie de session '{cookie.name}' sans HttpOnly + Secure + SameSite=Strict.",
            )
        ]

    if not cookie.secure:
        cookie_findings.append(_finding("cookies-no-secure", "cookies", "Cookie sans Secure", "high", f"Cookie '{cookie.name}' sans Secure."))
    if not cookie.httponly:
        cookie_findings.append(_finding("cookies-no-httponly", "cookies", "Cookie sans HttpOnly", "medium", f"Cookie '{cookie.name}' sans HttpOnly."))
    if cookie.samesite is None:
        cookie_findings.append(_finding("cookies-no-samesite", "cookies", "Cookie sans SameSite", "medium", f"Cookie '{cookie.name}' sans SameSite."))
    if cookie.samesite == "None" and not cookie.secure:
        cookie_findings.append(
            _finding(
                "cookies-samesite-none-requires-secure",
                "cookies",
                "SameSite=None sans Secure",
                "high",
                f"Cookie '{cookie.name}' avec SameSite=None sans Secure.",
            )
        )
    if session_like and not cookie.has_host_prefix and not cookie.has_secure_prefix:
        cookie_findings.append(
            _finding(
                "cookies-no-host-secure-prefix",
                "cookies",
                "Cookie sensible sans préfixe __Host-/__Secure-",
                "info",
                f"Cookie sensible '{cookie.name}' sans préfixe __Host- ou __Secure-.",
            )
        )
    if third_party_like and not cookie.partitioned:
        cookie_findings.append(
            _finding(
                "cookies-no-partitioned",
                "cookies",
                "Cookie tiers sans Partitioned (CHIPS)",
                "low",
                f"Cookie tiers '{cookie.name}' sans Partitioned.",
            )
        )
    if session_like and cookie.max_age_seconds is not None and cookie.max_age_seconds > settings.session_max_age_seconds:
        cookie_findings.append(
            _finding(
                "cookies-session-expires-long",
                "cookies",
                "Cookie de session avec durée trop longue",
                "low",
                f"Cookie de session '{cookie.name}' avec Expires/Max-Age > 24h.",
            )
        )
    return cookie_findings


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
    settings = get_cookies_settings()
    for cookie in result.cookies:
        findings.extend(_normalize_cookie_structured(cookie, settings))

    if findings:
        return findings

    # Compatibilité rétroactive (tests/unitaires legacy construits à partir des messages bruts).
    for msg in result.findings:
        slug, title, severity = _cookie_msg_to_finding(msg)
        findings.append(_finding(slug, "cookies", title, severity, msg))
    return findings


def _normalize_cache(result: CacheCheckResult) -> list[Finding]:
    """Convertit CacheCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "cache-connection-failed",
                "cache",
                "En-têtes de cache inaccessibles",
                "high",
                MSG_HEADERS_UNAVAILABLE,
            ),
        )
        return findings

    for msg in result.findings:
        msg_lower = msg.lower()
        if "page sensible" in msg_lower and "cacheable publiquement" in msg_lower:
            findings.append(
                _finding(
                    "cache-sensitive-page-public",
                    "cache",
                    "Page sensible cacheable publiquement",
                    "high",
                    msg,
                ),
            )
        elif "sans en-tête cache-control explicite" in msg_lower:
            findings.append(
                _finding(
                    "cache-no-cache-control",
                    "cache",
                    "Absence de Cache-Control sur page sensible",
                    "medium",
                    msg,
                ),
            )
        elif "incohérence pragma/cache-control" in msg_lower:
            findings.append(
                _finding(
                    "cache-pragma-incoherent",
                    "cache",
                    "Incohérence Pragma / Cache-Control",
                    "low",
                    msg,
                ),
            )
        elif "asset immuable sans cache long" in msg_lower:
            findings.append(
                _finding(
                    "cache-immutable-no-long-cache",
                    "cache",
                    "Asset immuable sans cache long",
                    "info",
                    msg,
                ),
            )
        else:
            findings.append(
                _finding(
                    "cache-generic-issue",
                    "cache",
                    "Problème de configuration de cache",
                    "medium",
                    msg,
                ),
            )
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
    """Convertit PathCheckResult (directory_listing) en list[Finding].

    Gère exposed (listing 200) et exposed_403 (chemins sensibles retournant 403).
    """
    findings = _normalize_path_check_result(
        result,
        "directory_listing",
        title_fn=lambda pf: f"Directory listing : {pf.path}",
        severity_fn=lambda pf: pf.severity.lower(),
    )
    for pf in result.exposed_403:
        findings.append(
            _finding(
                "directory_listing-sensitive-403",
                "directory_listing",
                f"Répertoire sensible révélé : {pf.path}",
                pf.severity.lower(),
                pf.message,
            )
        )
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
    for v in result.vulnerable_versions:
        ev = f"{v.product} {v.version} (version minimale recommandée : {v.min_safe_version})"
        findings.append(
            _finding(
                "tech_fingerprinting-vulnerable-version",
                "tech_fingerprinting",
                f"Version potentiellement vulnérable : {v.product} {v.version}",
                "medium",
                ev,
            )
        )
    if result.server:
        findings.append(
            _finding(
                "tech_fingerprinting-server-detected",
                "tech_fingerprinting",
                "Serveur détecté",
                "info",
                f"Serveur détecté : {result.server}",
            )
        )
    if result.runtime:
        findings.append(
            _finding(
                "tech_fingerprinting-runtime-detected",
                "tech_fingerprinting",
                "Runtime détecté",
                "info",
                f"Runtime détecté : {result.runtime}",
            )
        )
    if result.framework_cms:
        txt = result.framework_cms if not result.framework_cms_version else f"{result.framework_cms} {result.framework_cms_version}"
        findings.append(
            _finding(
                "tech_fingerprinting-framework-detected",
                "tech_fingerprinting",
                "Framework/CMS détecté",
                "info",
                f"Framework/CMS détecté : {txt}",
            )
        )
    if not findings:
        findings.append(
            _finding(
                "tech_fingerprinting-stack-unknown",
                "tech_fingerprinting",
                "Stack non identifiée",
                "info",
                "Stack : non identifiée (ou masquée).",
            )
        )
    return findings


def _information_disclosure_msg_to_finding(msg: str) -> tuple[str, str, str]:
    """Mappe un message information_disclosure vers (slug, title, severity).

    Args:
        msg: Message brut du finding.

    Returns:
        tuple[str, str, str]: (slug, title, severity).
    """
    msg_lower = msg.lower()
    if "stack trace détectée" in msg_lower:
        return ("info-disclosure-stack-trace", "Stack trace dans la réponse", "high")
    if "message d'erreur debug" in msg_lower or "mode développement" in msg_lower:
        return ("info-disclosure-debug-mode", "Mode debug exposé", "medium")
    if "secret potentiel" in msg_lower:
        return ("info-disclosure-secret", "Secret potentiel dans la réponse", "critical")
    if "header de debug détecté" in msg_lower:
        return ("info-disclosure-debug-headers", "En-têtes de débogage exposés", "medium")
    if "version serveur exposée" in msg_lower:
        return ("info-disclosure-server-version", "Version serveur exposée", "low")
    if "version runtime exposée" in msg_lower or "x-powered-by" in msg_lower:
        return ("info-disclosure-powered-by-version", "Version runtime exposée", "low")
    if "x-aspnet-version" in msg_lower:
        return ("info-disclosure-aspnet-version", "Version ASP.NET exposée", "low")
    if "en-tête custom révélant" in msg_lower:
        return ("info-disclosure-custom-header", "En-tête custom révélant la stack", "low")
    if "réponse https indisponible" in msg_lower or "fuites d'information" in msg_lower:
        return ("info-disclosure-connection-failed", "Analyse fuites impossible", "info")
    return ("info-disclosure-generic", "Fuite d'information", "medium")


def _normalize_information_disclosure(result: InformationDisclosureCheckResult) -> list[Finding]:
    """Convertit InformationDisclosureCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "info-disclosure-connection-failed",
                "information_disclosure",
                "Analyse fuites d'information impossible",
                "info",
                "Réponse HTTPS indisponible pour analyser les fuites d'information.",
            ),
        )
        return findings
    for msg in result.findings:
        slug, title, severity = _information_disclosure_msg_to_finding(msg)
        findings.append(_finding(slug, "information_disclosure", title, severity, msg))
    return findings


def _cors_cross_origin_msg_to_finding(msg: str) -> tuple[str, str, str]:
    """Mappe un message CORS/cross-origin vers (slug, title, severity)."""
    msg_l = msg.lower()
    if "inaccessibles" in msg_l or "réponse https indisponible" in msg_l:
        return ("cors-connection-failed", "CORS et cross-origin inaccessibles", "high")
    if "allow-origin: *" in msg_l and "endpoint sensible" in msg_l:
        return ("cors-allow-origin-star-sensitive", "Access-Control-Allow-Origin: * sur endpoint sensible", "high")
    if "incohérence cors" in msg_l and "credentials" in msg_l and "allow-origin: *" in msg_l:
        return ("cors-credentials-origin-star", "Incohérence CORS (Credentials + Allow-Origin: *)", "critical")
    if "réflexion d'origine non validée" in msg_l:
        return ("cors-credentials-origin-reflection", "Réflexion d'origine non validée (CORS)", "critical")
    if "méthodes cors" in msg_l and "dangereuses" in msg_l:
        return ("cors-allow-methods-dangerous", "Méthodes CORS dangereuses exposées (PUT/DELETE/PATCH)", "info")
    if "en-tête sensible exposé" in msg_l or "expose-headers" in msg_l:
        return ("cors-expose-headers-sensitive", "En-tête sensible exposé (Access-Control-Expose-Headers)", "medium")
    if "cross-origin-resource-policy manquant" in msg_l and "page principale" in msg_l:
        return ("corp-missing-main", "Cross-Origin-Resource-Policy manquant (page principale)", "low")
    if "cross-origin-resource-policy manquant" in msg_l:
        return ("corp-missing", "Cross-Origin-Resource-Policy manquant", "low")
    if "mixed content" in msg_l and "http" in msg_l:
        return ("mixed-content-http-on-https", "Mixed content (HTTP sur page HTTPS)", "high")
    return ("cors-generic", "Problème CORS ou cross-origin", "medium")


def _normalize_cors_cross_origin(result: CorsCrossOriginCheckResult) -> list[Finding]:
    """Convertit CorsCrossOriginCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "cors-connection-failed",
                "cors_cross_origin",
                "CORS et cross-origin inaccessibles",
                "high",
                "CORS et cross-origin inaccessibles : réponse HTTPS indisponible.",
            ),
        )
        return findings
    for msg in result.findings:
        slug, title, severity = _cors_cross_origin_msg_to_finding(msg)
        findings.append(_finding(slug, "cors_cross_origin", title, severity, msg))
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
    cache: CacheCheckResult
    information_disclosure: InformationDisclosureCheckResult
    cors_cross_origin: CorsCrossOriginCheckResult
    integrity: IntegrityCheckResult


def _integrity_msg_to_finding(msg: str) -> tuple[str, str, str]:
    """Mappe un message d'intégrité vers (slug, title, severity).

    Args:
        msg: Message du finding brut.

    Returns:
        tuple[str, str, str]: (slug, title, severity).
    """
    msg_l = msg.lower()
    if "ressources externes sans sri" in msg_l:
        return ("integrity-sri-external-missing", "Ressources externes sans SRI", "medium")
    if "aucune content-security-policy détectée" in msg_l:
        return (
            "integrity-csp-not-present-advanced-checks-skipped",
            "CSP absente : tests avancés non appliqués",
            "info",
        )
    if "scripts inline sans nonce" in msg_l:
        return ("integrity-script-inline-no-nonce", "Scripts inline sans nonce avec CSP", "medium")
    if "champs password sans autocomplete explicite" in msg_l:
        return ("integrity-form-password-autocomplete", "Champs password sans autocomplete adapté", "low")
    if 'liens target="_blank" sans rel="noopener"' in msg_l:
        return ("integrity-target-blank-noopener", 'Liens target="_blank" sans noopener', "low")
    if "meta robots absente sur une page sensible" in msg_l:
        return ("integrity-meta-robots-missing", "Meta robots absente sur page sensible", "low")
    if "meta robots présente mais sans noindex" in msg_l:
        return ("integrity-meta-robots-no-noindex", "Meta robots sans noindex sur page sensible", "low")
    if "vérifications d'intégrité impossibles" in msg_l:
        return ("integrity-connection-failed", "Analyse d'intégrité impossible", "info")
    return ("integrity-generic", "Problème d'intégrité ou de sous-ressources", "medium")


def _normalize_integrity(result: IntegrityCheckResult) -> list[Finding]:
    """Convertit IntegrityCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        findings.append(
            _finding(
                "integrity-connection-failed",
                "integrity",
                "Analyse d'intégrité impossible",
                "info",
                "Vérifications d'intégrité impossibles : réponse HTTPS indisponible ou illisible.",
            ),
        )
        return findings
    for msg in result.findings:
        slug, title, severity = _integrity_msg_to_finding(msg)
        findings.append(_finding(slug, "integrity", title, severity, msg))
    return findings


_NORMALIZERS: list[tuple[str, Callable[[object], list[Finding]]]] = [
    ("tls", _normalize_tls),
    ("headers", _normalize_headers),
    ("cache", _normalize_cache),
    ("cookies", _normalize_cookies),
    ("exposed_files", _normalize_exposed_files),
    ("directory_listing", _normalize_directory_listing),
    ("robots_txt", _normalize_robots_txt),
    ("sitemap", _normalize_sitemap),
    ("tech_fingerprinting", _normalize_tech_fingerprinting),
    ("information_disclosure", _normalize_information_disclosure),
    ("cors_cross_origin", _normalize_cors_cross_origin),
    ("integrity", _normalize_integrity),
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
