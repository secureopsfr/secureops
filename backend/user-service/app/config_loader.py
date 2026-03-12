"""Chargement de configuration pour User Service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from common.config_base import (
    DatabaseSettings,
    GeneralSettings,
    RoutersSettings,
    ServerSettings,
    load_yaml,
    parse_database_settings,
    parse_router_config,
    parse_server_settings,
)


@dataclass(frozen=True)
class ApiKeysSettings:
    """Paramètres des clés API (API publique)."""

    max_per_user: int
    default_ttl_days: int
    allowed_ttl_days: list[int]


@dataclass(frozen=True)
class AppSettings:
    """Paramètres applicatifs agrégés."""

    general: GeneralSettings
    server: ServerSettings
    database: DatabaseSettings
    api_keys: ApiKeysSettings
    routers: RoutersSettings


def _parse_api_keys_settings(data: Dict[str, Any] | None) -> ApiKeysSettings:
    if data is None:
        data = {}
    default_ttl = data.get("default_ttl_days")
    default_ttl = int(default_ttl) if default_ttl is not None else 30
    allowed_raw = data.get("allowed_ttl_days", [0, 30, 90, 180, 365])
    allowed_ttl: list[int] = [int(v) if v is not None else 0 for v in allowed_raw]
    return ApiKeysSettings(
        max_per_user=int(data.get("max_per_user", 5)),
        default_ttl_days=default_ttl,
        allowed_ttl_days=allowed_ttl,
    )


@lru_cache(maxsize=1)
def settings() -> AppSettings:
    """Charge les paramètres de configuration (résultat mis en cache)."""
    root = Path(__file__).resolve().parents[1]
    cfg_path = root / "config" / "settings.yml"

    data = load_yaml(cfg_path)
    general_data = data.get("general", {})

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "La variable d'environnement DATABASE_URL n'est pas définie. " "Utilisez launch_dev.sh, docker-compose ou exportez-la manuellement."
        )

    general = GeneralSettings(
        service_name=str(general_data.get("service_name", "user-service")),
        environment=str(general_data.get("environment", "development")),
        cors_allow_origins=(
            list(general_data.get("cors_allow_origins", ["*"])) if isinstance(general_data.get("cors_allow_origins", ["*"]), list) else ["*"]
        ),
        database_url=database_url,
    )

    routers_data = data.get("routers", {})
    routers = RoutersSettings(
        health=parse_router_config(routers_data.get("health", {}), default_prefix="/api", default_tags=["health"]),
    )

    return AppSettings(
        general=general,
        server=parse_server_settings(data.get("server", {}), default_port=8011),
        database=parse_database_settings(data.get("database", {})),
        api_keys=_parse_api_keys_settings(data.get("api_keys")),
        routers=routers,
    )


__all__ = ["settings", "AppSettings", "GeneralSettings", "RoutersSettings", "ApiKeysSettings"]
