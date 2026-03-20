"""Configuration liste noire (roadmap 1.6.2)."""

from functools import lru_cache

from common.config_base import BlacklistSettings, parse_blacklist_settings

from app.config._base import _load_settings_yml


@lru_cache(maxsize=1)
def get_blacklist_settings() -> BlacklistSettings:
    """Charge la section blacklist depuis config/settings.yml."""
    data = _load_settings_yml()
    return parse_blacklist_settings(data.get("blacklist"))
