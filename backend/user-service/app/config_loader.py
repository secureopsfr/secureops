"""Chargement de configuration pour User Service."""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

settings = create_simple_settings("user-service", default_port=8011, caller_file=__file__)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
