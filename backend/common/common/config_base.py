"""Classes de configuration de base — module commun.

Fournit les dataclasses réutilisables par tous les ``config_loader.py``
des micro-services : ``DatabaseSettings``, ``ServerSettings``,
``RouterConfig``, ainsi que ``load_yaml()`` et la factory
``create_simple_settings()`` pour les services simples.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict

import yaml


@dataclass(frozen=True)
class DatabaseSettings:
    """Paramètres de connexion et de pool pour la base PostgreSQL."""

    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False
    connect_args: dict | None = None
    ssl_mode: str = "prefer"
    pool_logging: bool = False


@dataclass(frozen=True)
class ServerSettings:
    """Paramètres serveur."""

    host: str = "0.0.0.0"
    port: int = 8000


@dataclass(frozen=True)
class RouterConfig:
    """Configuration d'un router."""

    prefix: str = "/api"
    tags: list[str] | None = None


def load_yaml(path: Path) -> Dict[str, Any]:
    """Charge un fichier YAML.

    Args:
        path: chemin vers le fichier YAML.

    Returns:
        Dict[str, Any]: contenu du fichier YAML.
    """
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_database_settings(data: Dict[str, Any]) -> DatabaseSettings:
    """Construit un ``DatabaseSettings`` depuis un dict YAML.

    Args:
        data: section ``database`` du fichier YAML.

    Returns:
        DatabaseSettings: paramètres de pool DB.
    """
    return DatabaseSettings(
        pool_size=int(data.get("pool_size", 20)),
        max_overflow=int(data.get("max_overflow", 30)),
        pool_timeout=int(data.get("pool_timeout", 30)),
        pool_recycle=int(data.get("pool_recycle", 3600)),
        pool_pre_ping=bool(data.get("pool_pre_ping", True)),
        echo=bool(data.get("echo", False)),
        connect_args=data.get("connect_args"),
        ssl_mode=str(data.get("ssl_mode", "prefer")),
        pool_logging=bool(data.get("pool_logging", False)),
    )


def parse_server_settings(data: Dict[str, Any], default_port: int = 8000) -> ServerSettings:
    """Construit un ``ServerSettings`` depuis un dict YAML.

    Args:
        data: section ``server`` du fichier YAML.
        default_port: port par défaut si absent du YAML.

    Returns:
        ServerSettings: paramètres serveur.
    """
    return ServerSettings(
        host=str(data.get("host", "0.0.0.0")),
        port=int(data.get("port", default_port)),
    )


def parse_router_config(data: Dict[str, Any], default_prefix: str = "/api", default_tags: list[str] | None = None) -> RouterConfig:
    """Construit un ``RouterConfig`` depuis un dict YAML.

    Args:
        data: section d'un router dans le YAML.
        default_prefix: préfixe par défaut.
        default_tags: tags par défaut.

    Returns:
        RouterConfig: configuration du router.
    """
    if default_tags is None:
        default_tags = ["health"]
    return RouterConfig(
        prefix=str(data.get("prefix", default_prefix)),
        tags=list(data.get("tags", default_tags)),
    )


# ---------------------------------------------------------------------------
# Dataclasses et factory pour les services simples
# (metier-a, metier-b, metier-c, user-service, …)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeneralSettings:
    """Paramètres généraux d'un service simple."""

    service_name: str
    environment: str
    cors_allow_origins: list[str]
    database_url: str


@dataclass(frozen=True)
class RoutersSettings:
    """Configuration des routers d'un service simple."""

    health: RouterConfig


@dataclass(frozen=True)
class AppSettings:
    """Paramètres applicatifs agrégés d'un service simple."""

    general: GeneralSettings
    server: ServerSettings
    database: DatabaseSettings
    routers: RoutersSettings


def create_simple_settings(
    service_name: str,
    default_port: int,
    *,
    caller_file: str,
) -> Callable[[], AppSettings]:
    """Factory qui génère une fonction ``settings()`` pour un service simple.

    Tous les services dont la config se résume à *general / server / database /
    routers.health* peuvent utiliser cette factory au lieu de dupliquer un
    ``config_loader.py`` complet.

    Args:
        service_name: nom par défaut du service (ex. ``"metier-a-service"``).
        default_port: port par défaut si absent du YAML.
        caller_file: ``__file__`` du module appelant — sert à localiser le
            fichier ``config/settings.yml`` relatif à la racine du service.

    Returns:
        Callable[[], AppSettings]: fonction ``settings()`` prête à l'emploi.

    Usage dans ``app/config_loader.py`` d'un service::

        from common.config_base import create_simple_settings

        settings = create_simple_settings(
            "metier-a-service", 8008, caller_file=__file__,
        )
    """
    # caller_file = "<service>/app/config_loader.py"
    # parents[1] = "<service>/"  →  "<service>/config/settings.yml"
    _service_root = Path(caller_file).resolve().parents[1]

    @lru_cache(maxsize=1)
    def settings() -> AppSettings:
        cfg_path = _service_root / "config" / "settings.yml"

        data = load_yaml(cfg_path)
        general_data = data.get("general", {})

        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise RuntimeError(
                "La variable d'environnement DATABASE_URL n'est pas définie. " "Utilisez launch_dev.sh, docker-compose ou exportez-la manuellement."
            )

        cors_raw = general_data.get("cors_allow_origins", ["*"])
        general = GeneralSettings(
            service_name=str(general_data.get("service_name", service_name)),
            environment=str(general_data.get("environment", "development")),
            cors_allow_origins=list(cors_raw) if isinstance(cors_raw, list) else ["*"],
            database_url=database_url,
        )

        routers_data = data.get("routers", {})

        return AppSettings(
            general=general,
            server=parse_server_settings(data.get("server", {}), default_port=default_port),
            database=parse_database_settings(data.get("database", {})),
            routers=RoutersSettings(
                health=parse_router_config(routers_data.get("health", {})),
            ),
        )

    return settings
