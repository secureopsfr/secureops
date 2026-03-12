"""Tests unitaires du chargeur de configuration gateway."""

import pytest

import app.config_loader as config_loader_module
from app.config_loader import get_services_config, load_config, reset_settings_cache, settings


def test_load_config_raises_value_error_on_invalid_config(monkeypatch) -> None:
    """Doit lever ValueError lorsque la config YAML est invalide."""

    def fake_read_yaml():  # type: ignore[no-untyped-def]
        return {"general": {"project_name": "x"}}  # structure incomplète

    monkeypatch.setattr(config_loader_module, "_read_yaml", fake_read_yaml)
    with pytest.raises(ValueError, match="Configuration invalide"):
        load_config()


def test_settings_is_cached(monkeypatch) -> None:
    """settings() ne doit charger la config qu'une seule fois avec le cache."""
    call_count = {"value": 0}

    def fake_load_config():  # type: ignore[no-untyped-def]
        call_count["value"] += 1
        return config_loader_module.Settings(
            general=config_loader_module.GeneralConf(project_name="gateway", debug=False, is_docker=False),
            cors=config_loader_module.CorsConf(
                allow_origins=["http://localhost:3000"],
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=True,
            ),
            services=config_loader_module.ServicesConf(
                docker={"scan": config_loader_module.ServiceConf(prefix="scan", url="http://scan:8012")},
                local={"scan": config_loader_module.ServiceConf(prefix="scan", url="http://localhost:8012")},
            ),
            timeouts=config_loader_module.TimeoutsConf(request_timeout=20.0, crawl_timeout=90.0),
            headers=config_loader_module.HeadersConf(hop_by_hop=["connection"]),
        )

    reset_settings_cache()
    monkeypatch.setattr(config_loader_module, "load_config", fake_load_config)

    first = settings()
    second = settings()

    assert first.general.project_name == "gateway"
    assert second.general.project_name == "gateway"
    assert call_count["value"] == 1


def test_get_services_config_uses_local_when_not_docker(monkeypatch) -> None:
    """Doit retourner la config locale si is_docker=False."""

    def fake_settings():  # type: ignore[no-untyped-def]
        return config_loader_module.Settings(
            general=config_loader_module.GeneralConf(project_name="gateway", debug=False, is_docker=False),
            cors=config_loader_module.CorsConf(
                allow_origins=["http://localhost:3000"],
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=True,
            ),
            services=config_loader_module.ServicesConf(
                docker={"scan": config_loader_module.ServiceConf(prefix="scan", url="http://scan:8012")},
                local={"scan": config_loader_module.ServiceConf(prefix="scan", url="http://localhost:8012")},
            ),
            timeouts=config_loader_module.TimeoutsConf(request_timeout=20.0, crawl_timeout=90.0),
            headers=config_loader_module.HeadersConf(hop_by_hop=["connection"]),
        )

    monkeypatch.setattr(config_loader_module, "settings", fake_settings)
    services = get_services_config()

    assert services == [{"prefix": "scan", "url": "http://localhost:8012"}]
