"""Base pour le chargement de configuration (settings.yml)."""

from functools import lru_cache
from pathlib import Path

from common.config_base import load_yaml


@lru_cache(maxsize=1)
def _load_settings_yml() -> dict:
    """Charge config/settings.yml une fois (mis en cache)."""
    root = Path(__file__).resolve().parents[2]  # pdf-service root (app/config/_base.py)
    return load_yaml(root / "config" / "settings.yml")
