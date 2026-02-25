"""Module pour charger la configuration depuis le fichier settings.yml.

Ce module charge et expose la configuration du service gateway
depuis le fichier config/settings.yml.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, ValidationError


class GeneralConf(BaseModel):
    """Configuration générale du service."""

    project_name: str
    debug: bool
    is_docker: bool


class CorsConf(BaseModel):
    """Configuration CORS."""

    allow_origins: List[str]
    allow_methods: List[str]
    allow_headers: List[str]
    allow_credentials: bool


class ServiceConf(BaseModel):
    """Configuration d'un service."""

    prefix: str
    url: str


class ServicesConf(BaseModel):
    """Configuration des services par environnement."""

    docker: Dict[str, ServiceConf]
    local: Dict[str, ServiceConf]


class TimeoutsConf(BaseModel):
    """Configuration des timeouts."""

    request_timeout: float


class HeadersConf(BaseModel):
    """Configuration des headers."""

    hop_by_hop: List[str]


class ContentTypesConf(BaseModel):
    """Configuration des types de contenu."""

    vector_tile: str


class Settings(BaseModel):
    """Configuration complète du service."""

    general: GeneralConf
    cors: CorsConf
    services: ServicesConf
    timeouts: TimeoutsConf
    headers: HeadersConf
    content_types: ContentTypesConf


def _read_yaml() -> dict:
    """Lit le fichier YAML de configuration."""
    cfg_path = Path(__file__).parent.parent / "config" / "settings.yml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file {cfg_path} not found")

    config_data = yaml.safe_load(cfg_path.read_text())

    # Mettre à jour is_docker depuis l'environnement
    import os

    is_docker = os.environ.get("IS_DOCKER", "false").lower() == "true"
    if config_data.get("general"):
        config_data["general"]["is_docker"] = is_docker

    return config_data


def load_config() -> Settings:
    """
    Construit un objet Settings à partir du YAML.

    Args:
        None

    Returns:
        Settings: Objet Settings construit à partir du YAML.

    Raises:
        ValidationError: Si la configuration YAML ne correspond pas au schéma Settings.
    """
    try:
        config_data = _read_yaml()
        return Settings(**config_data)
    except ValidationError as e:
        raise ValidationError(f"Configuration invalide: {e}")


@lru_cache
def settings() -> Settings:
    """
    Retourne les paramètres de configuration du service.

    Cette fonction est mise en cache pour éviter de recharger le fichier
    de configuration à chaque appel.

    Args:
        None

    Returns:
        Settings: Configuration du service.
    """
    return load_config()


def reset_settings_cache():
    """Réinitialise le cache de la fonction settings()."""
    settings.cache_clear()


def get_services_config() -> List[Dict[str, str]]:
    """
    Retourne la configuration des services selon l'environnement.

    Args:
        None

    Returns:
        List[Dict[str, str]]: Liste des services configurés pour l'environnement actuel.
    """
    config = settings()
    is_docker = config.general.is_docker

    if is_docker:
        services = config.services.docker
    else:
        services = config.services.local

    return [{"prefix": service.prefix, "url": service.url} for service in services.values()]
