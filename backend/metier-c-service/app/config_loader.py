"""Chargement de configuration pour Metier C Service."""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

settings = create_simple_settings("metier-c-service", default_port=8012, caller_file=__file__)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
