"""Tests unitaires pour common.url_utils."""

import pytest

from common.url_utils import URLValidationError, normalize_scan_url


def test_accepte_http_simple() -> None:
    """Accepte une URL http sans port explicite."""
    assert normalize_scan_url("http://example.com") == "http://example.com/"
    assert normalize_scan_url("http://example.com/") == "http://example.com/"


def test_accepte_https_simple() -> None:
    """Accepte une URL https sans port explicite."""
    assert normalize_scan_url("https://example.com") == "https://example.com/"
    assert normalize_scan_url("https://example.com/path") == "https://example.com/path"


def test_ajoute_https_si_sans_schema() -> None:
    """Ajoute https:// si aucun schéma n'est fourni."""
    assert normalize_scan_url("example.com") == "https://example.com/"
    assert normalize_scan_url("example.com/foo") == "https://example.com/foo"


def test_refuse_schema_non_http() -> None:
    """Refuse les schémas autres que http/https."""
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        normalize_scan_url("file:///etc/passwd")
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        normalize_scan_url("ftp://example.com")
    with pytest.raises(URLValidationError, match="Seuls les schémas http et https"):
        normalize_scan_url("javascript:alert(1)")


def test_refuse_credentials_dans_url() -> None:
    """Refuse user:pass@host."""
    with pytest.raises(URLValidationError, match="credentials"):
        normalize_scan_url("http://user:pass@example.com")
    with pytest.raises(URLValidationError, match="credentials"):
        normalize_scan_url("https://admin@example.com")


def test_refuse_url_trop_longue() -> None:
    """Refuse les URLs dépassant la longueur max."""
    with pytest.raises(URLValidationError, match="trop longue"):
        normalize_scan_url("http://example.com/" + "a" * 2048)


def test_refuse_url_vide() -> None:
    """Refuse les URLs vides ou invalides."""
    with pytest.raises(URLValidationError, match="vide"):
        normalize_scan_url("")
    with pytest.raises(URLValidationError, match="vide"):
        normalize_scan_url("   ")


def test_refuse_netloc_vide() -> None:
    """Refuse les URLs sans host."""
    with pytest.raises(URLValidationError, match="sans host"):
        normalize_scan_url("http://")
    with pytest.raises(URLValidationError, match="sans host"):
        normalize_scan_url("http:///path")


def test_normalise_minuscules_et_sans_fragment() -> None:
    """Normalise le netloc en minuscules et supprime le fragment."""
    result = normalize_scan_url("https://EXAMPLE.COM/path#anchor")
    assert result == "https://example.com/path"
    assert "#" not in result


def test_max_length_parametrable() -> None:
    """Respecte le paramètre max_length."""
    short_url = "https://a.com/"
    assert normalize_scan_url(short_url, max_length=20) == short_url
    # URL 19 chars > max_length=10
    with pytest.raises(URLValidationError, match="trop longue"):
        normalize_scan_url("https://example.com", max_length=10)
