"""Chargement de configuration pour Metier A Service."""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

settings = create_simple_settings("metier-a-service", default_port=8008, caller_file=__file__)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
