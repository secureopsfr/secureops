"""Tests unitaires du validateur d'URL (scan-service)."""

import pytest

from app.utils.url_validator import URLValidationError, validate_and_normalize_url


def test_accepte_http_simple() -> None:
    """Accepte une URL http sans port explicite."""
    assert validate_and_normalize_url("http://example.com") == "http://example.com/"
    assert validate_and_normalize_url("http://example.com/") == "http://example.com/"


def test_accepte_https_simple() -> None:
    """Accepte une URL https sans port explicite."""
    assert validate_and_normalize_url("https://example.com") == "https://example.com/"
    assert validate_and_normalize_url("https://example.com/path") == "https://example.com/path"


def test_accepte_ports_80_443() -> None:
    """Accepte les ports 80 et 443 explicites."""
    assert "://example.com:80/" in validate_and_normalize_url("http://example.com:80")
    assert "://example.com:443/" in validate_and_normalize_url("https://example.com:443")


def test_accepte_ports_badssl_tls() -> None:
    """Accepte les ports 1010 et 1011 (badssl.com TLS 1.0/1.1)."""
    assert "://tls-v1-0.badssl.com:1010/" in validate_and_normalize_url("https://tls-v1-0.badssl.com:1010")
    assert "://tls-v1-1.badssl.com:1011/" in validate_and_normalize_url("https://tls-v1-1.badssl.com:1011")


def test_refuse_schema_non_http() -> None:
    """Refuse les schémas autres que http/https."""
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        validate_and_normalize_url("file:///etc/passwd")
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        validate_and_normalize_url("ftp://example.com")
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        validate_and_normalize_url("javascript:alert(1)")


def test_refuse_credentials_dans_url() -> None:
    """Refuse user:pass@host."""
    with pytest.raises(URLValidationError, match="credentials"):
        validate_and_normalize_url("http://user:pass@example.com")
    with pytest.raises(URLValidationError, match="credentials"):
        validate_and_normalize_url("https://admin@example.com")


def test_refuse_port_non_autorise() -> None:
    """Refuse les ports non autorisés (ex. 8080, 8443)."""
    with pytest.raises(URLValidationError, match="ports .+ sont autorisés"):
        validate_and_normalize_url("http://example.com:8080")
    with pytest.raises(URLValidationError, match="ports .+ sont autorisés"):
        validate_and_normalize_url("https://example.com:8443")


def test_refuse_url_trop_longue() -> None:
    """Refuse les URLs dépassant la longueur max."""
    with pytest.raises(URLValidationError, match="trop longue"):
        validate_and_normalize_url("http://example.com/" + "a" * 2048)


def test_refuse_netloc_vide() -> None:
    """Refuse les URLs sans host."""
    with pytest.raises(URLValidationError, match="sans host|netloc"):
        validate_and_normalize_url("http://")
    with pytest.raises(URLValidationError, match="sans host|netloc"):
        validate_and_normalize_url("http:///path")


def test_normalise_minuscules_et_sans_fragment() -> None:
    """Normalise schéma/netloc en minuscules et supprime le fragment."""
    assert validate_and_normalize_url("HTTP://EXAMPLE.COM/page#anchor") == "http://example.com/page"


def test_refuse_url_vide() -> None:
    """Refuse une chaîne vide."""
    with pytest.raises(URLValidationError, match="vide"):
        validate_and_normalize_url("")
    with pytest.raises(URLValidationError, match="vide"):
        validate_and_normalize_url("   ")
