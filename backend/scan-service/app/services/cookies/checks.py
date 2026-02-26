"""Vérifications des flags de sécurité des cookies (roadmap §3.3).

Parse les en-têtes Set-Cookie et vérifie Secure, HttpOnly, SameSite.
Détecte les cookies sans Secure sur site HTTPS.
"""

from dataclasses import dataclass

import httpx


@dataclass
class CookieInfo:
    """Informations sur un cookie analysé.

    Attributes:
        name (str): Nom du cookie.
        secure (bool): True si le flag Secure est présent.
        httponly (bool): True si le flag HttpOnly est présent.
        samesite (str | None): Valeur SameSite (Strict, Lax, None) ou None si absent.
    """

    name: str
    secure: bool
    httponly: bool
    samesite: str | None


@dataclass
class CookieCheckResult:
    """Résultat des vérifications cookies.

    Attributes:
        cookies (tuple[CookieInfo, ...]): Liste des cookies analysés.
        findings (tuple[str, ...]): Liste des findings.
        fetch_ok (bool): True si la réponse a pu être analysée.
    """

    cookies: tuple[CookieInfo, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise le résultat pour l'événement SSE result."""
        cookies_serialized = [{"name": c.name, "secure": c.secure, "httponly": c.httponly, "samesite": c.samesite} for c in self.cookies]
        return {
            "cookies": cookies_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


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

    secure = False
    httponly = False
    samesite: str | None = None

    for part in parts[1:]:
        part_lower = part.lower()
        if part_lower == "secure":
            secure = True
        elif part_lower == "httponly":
            httponly = True
        elif part_lower.startswith("samesite="):
            val = part.split("=", 1)[1].strip().lower()
            if val in ("strict", "lax", "none"):
                samesite = val.capitalize() if val != "none" else "None"

    return CookieInfo(name=name, secure=secure, httponly=httponly, samesite=samesite)


def _findings_for_cookie(parsed: CookieInfo, is_https: bool) -> list[str]:
    """Génère les findings pour un cookie analysé."""
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


def check_cookies_from_response(response: httpx.Response | None, *, is_https: bool = True) -> CookieCheckResult:
    """Vérifie les flags de sécurité des cookies sur une réponse HTTPS.

    Analyse les en-têtes Set-Cookie et produit des findings pour :
    - Cookies sans Secure sur site HTTPS
    - Cookies sans HttpOnly
    - Cookies sans SameSite (recommandation explicite)

    Args:
        response: Réponse HTTP (ou None si fetch échoué).
        is_https: True si le site est servi en HTTPS (pour la règle Secure).

    Returns:
        CookieCheckResult: Cookies analysés et findings.
    """
    findings: list[str] = []
    cookies: list[CookieInfo] = []

    if response is None:
        findings.append("Impossible d'analyser les cookies (connexion refusée ou timeout).")
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
