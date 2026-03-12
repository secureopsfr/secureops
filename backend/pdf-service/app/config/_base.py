"""Base pour le chargement de configuration (settings.yml)."""

from common.config_base import create_load_settings_yml

_load_settings_yml = create_load_settings_yml(__file__, depth=2)
