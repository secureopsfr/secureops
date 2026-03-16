"""Normalisation des résultats Cookies en list[Finding].

Le fallback legacy (correspondance de chaînes sur result.findings) a été supprimé.
La normalisation utilise exclusivement les attributs structurés de CookieInfo.
"""

from app.catalogue.recommendations import get_recommendation, get_references
from app.config_loader import get_cookies_settings
from app.models.finding import Finding
from app.services.passive.both.cookies.checks import CookieCheckResult, CookieInfo


def _finding(slug: str, category: str, title: str, severity: str, evidence: str) -> Finding:
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


def _normalize_cookie_structured(cookie: CookieInfo, settings) -> list[Finding]:
    """Normalise un cookie à partir de ses attributs structurés."""
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


def normalize(result: CookieCheckResult) -> list[Finding]:
    """Convertit CookieCheckResult en list[Finding] via les attributs structurés."""
    if not result.fetch_ok:
        from app.constants import MSG_COOKIES_UNAVAILABLE

        return [_finding("cookies-connection-failed", "cookies", "Cookies inaccessibles", "high", MSG_COOKIES_UNAVAILABLE)]

    settings = get_cookies_settings()
    findings: list[Finding] = []
    for cookie in result.cookies:
        findings.extend(_normalize_cookie_structured(cookie, settings))
    return findings
