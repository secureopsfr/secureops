"""Tests pour common.url_helpers."""

from common.url_helpers import build_url_with_path, extract_host_from_url, extract_port_from_url, get_host_from_url


def test_extract_host_from_url() -> None:
    """Extrait le hostname sans port."""
    assert extract_host_from_url("https://example.com/path") == "example.com"
    assert extract_host_from_url("http://example.com:8080/") == "example.com"
    assert extract_host_from_url("https://[::1]/") == "::1"


def test_extract_port_from_url() -> None:
    """Extrait le port explicite."""
    assert extract_port_from_url("https://example.com:443/") == 443
    assert extract_port_from_url("http://example.com:8080/") == 8080
    assert extract_port_from_url("https://example.com/") is None


def test_build_url_with_path() -> None:
    """Construit URL base + chemin."""
    assert build_url_with_path("https://example.com/", ".env") == "https://example.com/.env"
    assert build_url_with_path("https://example.com", "foo/bar") == "https://example.com/foo/bar"


def test_get_host_from_url_alias() -> None:
    """get_host_from_url = extract_host_from_url."""
    url = "https://test.example.com/path"
    assert get_host_from_url(url) == extract_host_from_url(url)
