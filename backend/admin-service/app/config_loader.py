"""Chargement de configuration pour Admin Service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from common.config_base import (
    DatabaseSettings,
    RouterConfig,
    ServerSettings,
    load_yaml,
    parse_database_settings,
    parse_router_config,
    parse_server_settings,
)


@dataclass(frozen=True)
class QueryLimitSettings:
    """Paramètres de validation pour les queries."""

    default: int
    ge: int
    description: str
    le: int | None = None


@dataclass(frozen=True)
class MetricsQueriesSettings:
    """Paramètres de validation des queries de métriques."""

    window_minutes: QueryLimitSettings
    limit: QueryLimitSettings


@dataclass(frozen=True)
class MetricsSettings:
    """Paramètres liés aux métriques internes."""

    api_key: str
    queries: MetricsQueriesSettings


@dataclass(frozen=True)
class GeneralSettings:
    """Paramètres généraux."""

    service_name: str
    environment: str
    cors_allow_origins: list[str]
    database_url: str


@dataclass(frozen=True)
class RoutersSettings:
    """Configuration des routers."""

    kpis: RouterConfig
    health: RouterConfig


@dataclass(frozen=True)
class AppSettings:
    """Paramètres applicatifs agrégés."""

    general: GeneralSettings
    server: ServerSettings
    metrics: MetricsSettings
    database: DatabaseSettings
    routers: RoutersSettings


def _get_env_or(value: str, env_key: str) -> str:
    if env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    return value


def _parse_metrics_settings(data: Dict[str, Any] | None) -> MetricsSettings:
    if data is None:
        data = {}
    queries_data = data.get("queries", {})
    window_minutes_data = queries_data.get("window_minutes", {})
    limit_data = queries_data.get("limit", {})
    return MetricsSettings(
        api_key=_get_env_or(str(data.get("api_key", "")), "ADMIN_METRICS_API_KEY"),
        queries=MetricsQueriesSettings(
            window_minutes=QueryLimitSettings(
                default=int(window_minutes_data.get("default", 10080)),
                ge=int(window_minutes_data.get("ge", 1)),
                le=int(window_minutes_data.get("le")) if window_minutes_data.get("le") is not None else None,
                description=str(window_minutes_data.get("description", "")),
            ),
            limit=QueryLimitSettings(
                default=int(limit_data.get("default", 50)),
                ge=int(limit_data.get("ge", 1)),
                le=int(limit_data.get("le", 200)),
                description=str(limit_data.get("description", "")),
            ),
        ),
    )


@lru_cache(maxsize=1)
def settings() -> AppSettings:
    """Charge les paramètres de configuration (résultat mis en cache)."""
    root = Path(__file__).resolve().parents[1]
    cfg_path = root / "config" / "settings.yml"

    data = load_yaml(cfg_path)

    general_data = data.get("general", {})

    # DATABASE_URL doit provenir de l'environnement (launch_dev.sh / docker-compose / .env)
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "La variable d'environnement DATABASE_URL n'est pas définie. " "Utilisez launch_dev.sh, docker-compose ou exportez-la manuellement."
        )

    general_settings = GeneralSettings(
        service_name=str(general_data.get("service_name", "admin-service")),
        environment=str(general_data.get("environment", "development")),
        cors_allow_origins=(
            list(general_data.get("cors_allow_origins", ["*"])) if isinstance(general_data.get("cors_allow_origins", ["*"]), list) else ["*"]
        ),
        database_url=database_url,
    )

    server_settings = parse_server_settings(data.get("server", {}), default_port=8010)
    metrics_settings = _parse_metrics_settings(data.get("metrics") or {})
    database_settings = parse_database_settings(data.get("database", {}))

    # Parser routers
    routers_data = data.get("routers", {})
    routers_settings = RoutersSettings(
        kpis=parse_router_config(routers_data.get("kpis", {}), default_prefix="/api/metrics", default_tags=["metrics"]),
        health=parse_router_config(routers_data.get("health", {}), default_prefix="/api", default_tags=["health"]),
    )

    return AppSettings(
        general=general_settings,
        server=server_settings,
        metrics=metrics_settings,
        database=database_settings,
        routers=routers_settings,
    )
