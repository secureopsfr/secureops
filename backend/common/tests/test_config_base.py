"""Tests unitaires pour common.config_base."""

from pathlib import Path

import pytest

from common.config_base import (
    DatabaseSettings,
    ServerSettings,
    load_yaml,
    parse_database_settings,
    parse_router_config,
    parse_server_settings,
)


def test_load_yaml(tmp_path: Path) -> None:
    """load_yaml charge un fichier YAML valide."""
    yaml_file = tmp_path / "test.yml"
    yaml_file.write_text("key: value\nnested:\n  a: 1")
    data = load_yaml(yaml_file)
    assert data["key"] == "value"
    assert data["nested"]["a"] == 1


def test_load_yaml_empty_returns_dict(tmp_path: Path) -> None:
    """load_yaml retourne un dict vide pour fichier vide."""
    yaml_file = tmp_path / "empty.yml"
    yaml_file.write_text("")
    data = load_yaml(yaml_file)
    assert data == {}


def test_parse_database_settings_defaults() -> None:
    """parse_database_settings utilise les valeurs par défaut si absent."""
    settings = parse_database_settings({})
    assert settings.pool_size == 20
    assert settings.max_overflow == 30
    assert settings.pool_pre_ping is True


def test_parse_database_settings_overrides() -> None:
    """parse_database_settings utilise les valeurs du dict."""
    data = {"pool_size": 10, "max_overflow": 5}
    settings = parse_database_settings(data)
    assert settings.pool_size == 10
    assert settings.max_overflow == 5


def test_parse_server_settings() -> None:
    """parse_server_settings extrait host et port."""
    settings = parse_server_settings({"host": "127.0.0.1", "port": 9000})
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000


def test_parse_server_settings_default_port() -> None:
    """parse_server_settings utilise default_port si port absent."""
    settings = parse_server_settings({}, default_port=8012)
    assert settings.port == 8012
    assert settings.host == "0.0.0.0"


def test_parse_router_config() -> None:
    """parse_router_config extrait prefix et tags."""
    config = parse_router_config({"prefix": "/v1", "tags": ["api"]})
    assert config.prefix == "/v1"
    assert config.tags == ["api"]


def test_parse_router_config_defaults() -> None:
    """parse_router_config utilise les défauts."""
    config = parse_router_config({})
    assert config.prefix == "/api"
    assert "health" in config.tags


def test_database_settings_frozen() -> None:
    """DatabaseSettings est immuable."""
    s = DatabaseSettings(pool_size=10)
    with pytest.raises(AttributeError):
        s.pool_size = 20  # type: ignore[misc]


def test_server_settings_frozen() -> None:
    """ServerSettings est immuable (frozen dataclass)."""
    s = ServerSettings(port=8000)
    with pytest.raises(AttributeError):
        s.port = 9000  # type: ignore[misc]
