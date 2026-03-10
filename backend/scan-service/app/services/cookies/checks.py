"""Vérifications des flags de sécurité des cookies (roadmap §3.3).

Parse les en-têtes Set-Cookie et vérifie Secure, HttpOnly, SameSite.
Détecte les cookies sans Secure sur site HTTPS.
Extensions v0.2.0 : préfixes __Host-/__Secure-, Partitioned (CHIPS),
cookie de session sans triple protection, Expires trop lointain.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from app.config_loader import get_cookies_settings
from app.constants import MSG_COOKIES_UNAVAILABLE


@dataclass
class CookieInfo:
    """Informations sur un cookie analysé.

    Attributes:
        name: Nom du cookie.
        secure: True si le flag Secure est présent.
        httponly: True si le flag HttpOnly est présent.
        samesite: Valeur SameSite (Strict, Lax, None) ou None si absent.
        has_host_prefix: True si le nom commence par __Host-.
        has_secure_prefix: True si le nom commence par __Secure-.
        partitioned: True si l'attribut Partitioned est présent.
        expires_at: Date d'expiration (Expires) ou None.
        max_age_seconds: Max-Age en secondes ou None.
    """

    name: str
    secure: bool
    httponly: bool
    samesite: str | None
    has_host_prefix: bool = False
    has_secure_prefix: bool = False
    partitioned: bool = False
    expires_at: datetime | None = None
    max_age_seconds: int | None = None


@dataclass
class CookieCheckResult:
    """Résultat des vérifications cookies.

    Attributes:
        cookies: Liste des cookies analysés.
        findings: Liste des findings.
        fetch_ok: True si la réponse a pu être analysée.
    """

    cookies: tuple[CookieInfo, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise le résultat pour l'événement SSE result."""
        cookies_serialized = [
            {
                "name": c.name,
                "secure": c.secure,
                "httponly": c.httponly,
                "samesite": c.samesite,
                "has_host_prefix": c.has_host_prefix,
                "has_secure_prefix": c.has_secure_prefix,
                "partitioned": c.partitioned,
            }
            for c in self.cookies
        ]
        return {
            "cookies": cookies_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def _is_session_like(name: str) -> bool:
    """Indique si le nom du cookie suggère une session ou authentification."""
    name_lower = name.lower()
    return any(pat in name_lower for pat in get_cookies_settings().session_like_names)


def _is_third_party_like(name: str) -> bool:
    """Indique si le nom du cookie suggère un cookie tiers (analytics, etc.)."""
    name_lower = name.lower()
    return any(pat in name_lower for pat in get_cookies_settings().third_party_like_names)


def _parse_samesite(part: str) -> str | None:
    """Extrait la valeur SameSite d'un attribut (ex. SameSite=Strict)."""
    val = part.split("=", 1)[1].strip().lower()
    if val in ("strict", "lax", "none"):
        return val.capitalize() if val != "none" else "None"
    return None


def _parse_expires(part: str) -> datetime | None:
    """Parse l'attribut Expires (RFC 2822)."""
    val = part.split("=", 1)[1].strip()
    try:
        dt = parsedate_to_datetime(val)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except (ValueError, TypeError):
        return None


def _parse_max_age(part: str) -> int | None:
    """Extrait Max-Age en secondes."""
    try:
        return int(part.split("=", 1)[1].strip().split()[0])
    except (ValueError, IndexError):
        return None


def _parse_set_cookie_header(header_value: str) -> CookieInfo | None:
    """Parse un en-tête Set-Cookie et extrait nom + flags.

    Args:
        header_value: Valeur brute de l'en-tête Set-Cookie.

    Returns:
        CookieInfo | None: Cookie parsé ou None si invalide.
    """
    parts = [p.strip() for p in header_value.split(";")]
    if not parts or "=" not in parts[0]:
        return None
    name = parts[0].split("=", 1)[0].strip()
    if not name:
        return None

    attrs = {"secure": False, "httponly": False, "samesite": None, "partitioned": False}
    expires_at: datetime | None = None
    max_age_seconds: int | None = None

    for part in parts[1:]:
        part_lower = part.lower()
        if part_lower == "secure":
            attrs["secure"] = True
        elif part_lower == "httponly":
            attrs["httponly"] = True
        elif part_lower == "partitioned":
            attrs["partitioned"] = True
        elif part_lower.startswith("samesite="):
            attrs["samesite"] = _parse_samesite(part)
        elif part_lower.startswith("expires="):
            expires_at = _parse_expires(part)
        elif part_lower.startswith("max-age="):
            max_age_seconds = _parse_max_age(part)

    return CookieInfo(
        name=name,
        secure=attrs["secure"],
        httponly=attrs["httponly"],
        samesite=attrs["samesite"],
        has_host_prefix=name.startswith("__Host-"),
        has_secure_prefix=name.startswith("__Secure-"),
        partitioned=attrs["partitioned"],
        expires_at=expires_at,
        max_age_seconds=max_age_seconds,
    )


def _session_has_triple_protection(parsed: CookieInfo) -> bool:
    """Indique si le cookie a HttpOnly + Secure + SameSite=Strict."""
    return parsed.httponly and parsed.secure and parsed.samesite == "Strict"


def _session_expires_too_long(parsed: CookieInfo) -> bool:
    """Indique si un cookie session a Expires/Max-Age > 24h."""
    max_age_limit = get_cookies_settings().session_max_age_seconds
    if parsed.max_age_seconds is not None and parsed.max_age_seconds > max_age_limit:
        return True
    if parsed.expires_at is None:
        return False
    now = datetime.now(timezone.utc)
    if parsed.expires_at <= now:
        return False
    return (parsed.expires_at - now).total_seconds() > max_age_limit


def _findings_base_flags(parsed: CookieInfo, is_https: bool) -> list[str]:
    """Findings pour Secure, HttpOnly, SameSite (flags de base)."""
    findings: list[str] = []
    if is_https and not parsed.secure:
        findings.append(f"Cookie '{parsed.name}' sans Secure sur site HTTPS : risque d'interception.")
    if not parsed.httponly:
        findings.append(f"Cookie '{parsed.name}' sans HttpOnly : accessible en JavaScript, risque XSS.")
    if parsed.samesite is None:
        findings.append(f"Cookie '{parsed.name}' sans SameSite explicite : configurer Strict ou Lax.")
    if parsed.samesite == "None" and not parsed.secure:
        findings.append(f"Cookie '{parsed.name}' : SameSite=None requiert Secure.")
    return findings


def _findings_for_cookie(parsed: CookieInfo, is_https: bool) -> list[str]:
    """Génère les findings pour un cookie analysé."""
    session_like = _is_session_like(parsed.name)
    third_party_like = _is_third_party_like(parsed.name)

    if session_like and not _session_has_triple_protection(parsed):
        return [f"Cookie de session '{parsed.name}' sans HttpOnly + Secure + SameSite=Strict : risque élevé."]

    findings = _findings_base_flags(parsed, is_https)

    if session_like and not parsed.has_host_prefix and not parsed.has_secure_prefix:
        findings.append(f"Cookie sensible '{parsed.name}' sans préfixe __Host- ou __Secure- : bonne pratique recommandée.")
    if third_party_like and not parsed.partitioned:
        findings.append(f"Cookie '{parsed.name}' (analytics/tiers probable) sans Partitioned : recommandation CHIPS.")
    if session_like and _session_expires_too_long(parsed):
        findings.append(f"Cookie de session '{parsed.name}' avec Expires/Max-Age > 24h : session persistante non recommandée.")

    return findings


def check_cookies_from_response(response: httpx.Response | None, *, is_https: bool = True) -> CookieCheckResult:
    """Vérifie les flags de sécurité des cookies sur une réponse HTTPS.

    Analyse les en-têtes Set-Cookie et produit des findings pour :
    - Cookies sans Secure sur site HTTPS
    - Cookies sans HttpOnly
    - Cookies sans SameSite (recommandation explicite)
    - Cookies de session sans HttpOnly + Secure + SameSite=Strict
    - Préfixes __Host- / __Secure- (bonnes pratiques)
    - Partitioned (CHIPS) pour cookies tiers
    - Expires/Max-Age trop long pour session

    Args:
        response: Réponse HTTP (ou None si fetch échoué).
        is_https: True si le site est servi en HTTPS (pour la règle Secure).

    Returns:
        CookieCheckResult: Cookies analysés et findings.
    """
    findings: list[str] = []
    cookies: list[CookieInfo] = []

    if response is None:
        findings.append(MSG_COOKIES_UNAVAILABLE)
        return CookieCheckResult(cookies=(), findings=tuple(findings), fetch_ok=False)

    set_cookie_values: list[str] = []
    if hasattr(response.headers, "raw"):
        for key, value in response.headers.raw:
            if key.lower() == b"set-cookie":
                set_cookie_values.append(value.decode("utf-8", errors="replace"))

    for raw_value in set_cookie_values:
        parsed = _parse_set_cookie_header(raw_value)
        if parsed is None:
            continue
        cookies.append(parsed)
        findings.extend(_findings_for_cookie(parsed, is_https))

    return CookieCheckResult(
        cookies=tuple(cookies),
        findings=tuple(findings),
        fetch_ok=True,
    )
