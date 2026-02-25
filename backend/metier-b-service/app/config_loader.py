"""Chargement de configuration pour Metier B Service."""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

settings = create_simple_settings("metier-b-service", default_port=8009, caller_file=__file__)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
