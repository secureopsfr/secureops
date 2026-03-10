"""Configuration SSRF (roadmap §2.2)."""

from functools import lru_cache

from common.config_base import SsrfSettings, parse_ssrf_settings

from app.config._base import _load_settings_yml


@lru_cache(maxsize=1)
def get_ssrf_settings() -> SsrfSettings:
    """Charge la section SSRF depuis config/settings.yml."""
    data = _load_settings_yml()
    return parse_ssrf_settings(data.get("ssrf"))
