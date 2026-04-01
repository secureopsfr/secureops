"""Tests pour common.url_helpers."""

from common.url_helpers import (
    build_url_with_path,
    extract_host_from_url,
    extract_port_from_url,
    get_host_from_url,
    registered_domain_from_host,
    registered_domain_from_url,
)


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


def test_registered_domain_from_url_etld1() -> None:
    """eTLD+1 : www et sous-domaines se regroupent sur le domaine enregistrable."""
    assert registered_domain_from_url("https://blog.example.com/foo") == "example.com"
    assert registered_domain_from_url("https://www.example.com/") == "example.com"
    assert registered_domain_from_url("example.com") == "example.com"


def test_registered_domain_co_uk() -> None:
    """Suffixes composés (.co.uk)."""
    assert registered_domain_from_url("https://api.shop.example.co.uk/x") == "example.co.uk"


def test_registered_domain_from_host_port() -> None:
    """Port retiré avant extraction."""
    assert registered_domain_from_host("www.example.com:8443") == "example.com"


def test_registered_domain_ip_fallback() -> None:
    """IP : pas de suffixe public, retour hôte."""
    assert registered_domain_from_host("192.168.1.1") == "192.168.1.1"
