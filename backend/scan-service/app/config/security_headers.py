"""Configuration des Security Headers (roadmap §3.2)."""

import re
from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class SecurityHeaderConfig:
    """Configuration d'un en-tête de sécurité à vérifier."""

    name: str
    message_absent: str
    expected_value: str | None
    slug: str


_KNOWN_HEADER_SLUGS: dict[str, str] = {
    "Content-Security-Policy": "headers-csp-absent",
    "Strict-Transport-Security": "headers-hsts-absent",
    "X-Frame-Options": "headers-xfo-absent",
    "X-Content-Type-Options": "headers-xcto-absent",
    "Referrer-Policy": "headers-referrer-absent",
    "Permissions-Policy": "headers-permissions-absent",
}

_DEFAULT_HEADERS: tuple[tuple[str, str, str | None, str], ...] = (
    ("Content-Security-Policy", "Content-Security-Policy absent : risque XSS accru.", None, "headers-csp-absent"),
    ("Strict-Transport-Security", "Strict-Transport-Security absent : risque de downgrade HTTPS→HTTP.", None, "headers-hsts-absent"),
    ("X-Frame-Options", "X-Frame-Options absent : risque de clickjacking.", None, "headers-xfo-absent"),
    ("X-Content-Type-Options", "X-Content-Type-Options absent : risque de MIME sniffing.", "nosniff", "headers-xcto-absent"),
    ("Referrer-Policy", "Referrer-Policy absent : risque de fuite d'URLs sensibles.", None, "headers-referrer-absent"),
    ("Permissions-Policy", "Permissions-Policy absent : APIs navigateur accessibles par défaut.", None, "headers-permissions-absent"),
)


def _derive_header_slug(name: str) -> str:
    """Dérive un slug à partir du nom d'en-tête."""
    if name in _KNOWN_HEADER_SLUGS:
        return _KNOWN_HEADER_SLUGS[name]
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"headers-{normalized}-absent" if normalized else "headers-unknown-absent"


@lru_cache(maxsize=1)
def get_security_headers_settings() -> tuple[SecurityHeaderConfig, ...]:
    """Charge la section security_headers depuis config/settings.yml."""
    data = _load_settings_yml()
    sh = data.get("security_headers") or {}
    headers_raw = sh.get("headers") or []
    if not headers_raw:
        return tuple(SecurityHeaderConfig(h[0], h[1], h[2], h[3]) for h in _DEFAULT_HEADERS)
    result: list[SecurityHeaderConfig] = []
    for item in headers_raw:
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            msg = str(item.get("message_absent", ""))
            exp = item.get("expected_value")
            exp_val = str(exp) if exp is not None else None
            slug = str(item.get("slug", "")) if item.get("slug") else _derive_header_slug(name)
            result.append(SecurityHeaderConfig(name=name, message_absent=msg, expected_value=exp_val, slug=slug))
    return tuple(result)
