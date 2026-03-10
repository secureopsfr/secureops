"""Tests unitaires de l'authentification par clé API."""

import app.utils.api_key_auth as api_key_auth_module
from app.utils.api_key_auth import _get_user_service_url, extract_api_key_from_request


def test_extract_api_key_prefers_x_api_key() -> None:
    """X-API-Key doit être prioritaire sur Authorization."""
    extracted = extract_api_key_from_request("Bearer not-a-jwt", "my-key")
    assert extracted == "my-key"


def test_extract_api_key_from_bearer_non_jwt() -> None:
    """Authorization Bearer non-JWT doit être interprété comme clé API."""
    extracted = extract_api_key_from_request("Bearer sk_test_123", None)
    assert extracted == "sk_test_123"


def test_extract_api_key_ignores_jwt_bearer() -> None:
    """Authorization Bearer JWT ne doit pas être interprété comme clé API."""
    jwt_like = "header.payload.signature"
    extracted = extract_api_key_from_request(f"Bearer {jwt_like}", None)
    assert extracted is None


def test_get_user_service_url_is_cached(monkeypatch) -> None:
    """La résolution de l'URL user-service doit utiliser le cache local."""
    calls = {"value": 0}

    def fake_get_services_config():  # type: ignore[no-untyped-def]
        calls["value"] += 1
        return [{"prefix": "user", "url": "http://localhost:8011"}]

    _get_user_service_url.cache_clear()
    monkeypatch.setattr(api_key_auth_module, "get_services_config", fake_get_services_config)

    first = _get_user_service_url()
    second = _get_user_service_url()

    assert first == "http://localhost:8011"
    assert second == "http://localhost:8011"
    assert calls["value"] == 1
