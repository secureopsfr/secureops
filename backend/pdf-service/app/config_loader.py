"""Chargement de configuration pour PDF Service."""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

settings = create_simple_settings("pdf-service", default_port=8013, caller_file=__file__, require_database_url=False)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
