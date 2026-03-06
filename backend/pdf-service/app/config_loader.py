"""Chargement de configuration pour PDF Service."""

import os

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings

# Ce service n'utilise pas de BDD ; create_simple_settings exige DATABASE_URL → valeur factice si absente.
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://localhost/pdf_service_dummy"

settings = create_simple_settings("pdf-service", default_port=8013, caller_file=__file__)

__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings"]
