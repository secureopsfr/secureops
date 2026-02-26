"""Configuration validation d'URL (roadmap §2.1)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class UrlValidationSettings:
    """Configuration de la validation d'URL (schémas, ports, longueur max)."""

    max_url_length: int
    allowed_schemes: tuple[str, ...]
    allowed_ports: tuple[int, ...]


_DEFAULT_MAX_LENGTH = 2048
_DEFAULT_SCHEMES = ("http", "https")
_DEFAULT_PORTS = (80, 443)


@lru_cache(maxsize=1)
def get_url_validation_settings() -> UrlValidationSettings:
    """Charge la section url_validation depuis config/settings.yml."""
    data = _load_settings_yml()
    uv = data.get("url_validation") or {}
    max_len = int(uv.get("max_url_length", _DEFAULT_MAX_LENGTH))
    schemes = uv.get("allowed_schemes") or _DEFAULT_SCHEMES
    ports = uv.get("allowed_ports") or _DEFAULT_PORTS
    return UrlValidationSettings(
        max_url_length=max_len,
        allowed_schemes=tuple(str(s) for s in schemes),
        allowed_ports=tuple(int(p) for p in ports),
    )
