"""Configuration validation d'URL (roadmap §2.1)."""

from functools import lru_cache

from common.config_base import UrlValidationSettings, parse_url_validation_settings

from app.config._base import _load_settings_yml


@lru_cache(maxsize=1)
def get_url_validation_settings() -> UrlValidationSettings:
    """Charge la section url_validation depuis config/settings.yml."""
    data = _load_settings_yml()
    return parse_url_validation_settings(data.get("url_validation"))
