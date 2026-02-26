"""Tests unitaires pour les vérifications TLS/HTTPS (scan_runner)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.services.scan_runner import (
    _build_http_url,
    _build_https_url,
    _location_redirects_to_https,
    run_tls_checks,
)


def _make_valid_cert_der() -> bytes:
    """Génère un certificat valide (non auto-signé, dates OK) en DER pour les tests."""
    ca_key = rsa.generate_private_key(65537, 2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )
    leaf_key = rsa.generate_private_key(65537, 2048)
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])
    leaf_cert = (
        x509.CertificateBuilder()
        .subject_name(leaf_name)
        .issuer_name(ca_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )
    return leaf_cert.public_bytes(serialization.Encoding.DER)


def _make_expired_cert_der() -> bytes:
    """Génère un certificat expiré en DER pour les tests."""
    key = rsa.generate_private_key(65537, 2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=365))
        .not_valid_after(datetime.now(timezone.utc) - timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.DER)


def _make_self_signed_cert_der() -> bytes:
    """Génère un certificat auto-signé valide en DER pour les tests."""
    key = rsa.generate_private_key(65537, 2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.DER)


def test_build_https_url_from_http() -> None:
    """_build_https_url transforme http://host en https://host/."""
    assert _build_https_url("http://example.com") == "https://example.com/"
    assert _build_https_url("http://example.com/") == "https://example.com/"
    assert _build_https_url("http://example.com:80/path") == "https://example.com/"


def test_build_https_url_from_https() -> None:
    """_build_https_url transforme https://host en https://host/."""
    assert _build_https_url("https://example.com") == "https://example.com/"
    assert _build_https_url("https://example.com:443/") == "https://example.com/"


def test_build_http_url() -> None:
    """_build_http_url construit http://host/."""
    assert _build_http_url("https://example.com") == "http://example.com/"
    assert _build_http_url("http://example.com:80/path") == "http://example.com/"


def test_location_redirects_to_https() -> None:
    """_location_redirects_to_https détecte les URLs https."""
    assert _location_redirects_to_https("https://example.com/") is True
    assert _location_redirects_to_https("HTTPS://example.com") is True
    assert _location_redirects_to_https("http://example.com") is False
    assert _location_redirects_to_https("") is False
    assert _location_redirects_to_https(None) is False


@pytest.mark.asyncio()
async def test_run_tls_checks_https_ok_et_redirect_ok() -> None:
    """run_tls_checks retourne https_enabled=True, redirect OK et certificat valide."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 301
    mock_http_resp.headers = {"location": "https://example.com/"}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    valid_cert = _make_valid_cert_der()

    with (
        patch("app.services.scan_runner.httpx.AsyncClient") as mock_client,
        patch("app.services.scan_runner._fetch_certificate_der", return_value=valid_cert),
    ):
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://example.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is True
    assert result.certificate_status == "valid"
    assert len(result.findings) == 0


@pytest.mark.asyncio()
async def test_run_tls_checks_https_non_actif_connect_error() -> None:
    """run_tls_checks retourne https_enabled=False et un finding en cas de ConnectError."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("http://monsite.com")

    assert result.https_enabled is False
    assert result.http_redirects_to_https is None
    assert result.certificate_status is None
    assert len(result.findings) == 1
    assert "HTTPS non activé" in result.findings[0]
    assert "interception" in result.findings[0]


@pytest.mark.asyncio()
async def test_run_tls_checks_https_non_actif_timeout() -> None:
    """run_tls_checks retourne https_enabled=False en cas de timeout."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectTimeout("Timeout"))

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("http://example.com")

    assert result.https_enabled is False
    assert result.http_redirects_to_https is None
    assert result.certificate_status is None
    assert len(result.findings) == 1
    assert "HTTPS non activé" in result.findings[0]


@pytest.mark.asyncio()
async def test_run_tls_checks_pas_redirection_http() -> None:
    """run_tls_checks détecte l'absence de redirection HTTP→HTTPS (réponse 200)."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 200
    mock_http_resp.headers = {}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    valid_cert = _make_valid_cert_der()

    with (
        patch("app.services.scan_runner.httpx.AsyncClient") as mock_client,
        patch("app.services.scan_runner._fetch_certificate_der", return_value=valid_cert),
    ):
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://monsite.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is False
    assert result.certificate_status == "valid"
    assert len(result.findings) == 1
    assert "Pas de redirection HTTP→HTTPS" in result.findings[0]


@pytest.mark.asyncio()
async def test_run_tls_checks_certificat_expire() -> None:
    """run_tls_checks détecte un certificat expiré."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 301
    mock_http_resp.headers = {"location": "https://example.com/"}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    expired_cert = _make_expired_cert_der()

    with (
        patch("app.services.scan_runner.httpx.AsyncClient") as mock_client,
        patch("app.services.scan_runner._fetch_certificate_der", return_value=expired_cert),
    ):
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://example.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is True
    assert result.certificate_status == "expired"
    assert any("expiré" in f for f in result.findings)


@pytest.mark.asyncio()
async def test_run_tls_checks_certificat_auto_signe() -> None:
    """run_tls_checks détecte un certificat auto-signé."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 301
    mock_http_resp.headers = {"location": "https://example.com/"}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    self_signed_cert = _make_self_signed_cert_der()

    with (
        patch("app.services.scan_runner.httpx.AsyncClient") as mock_client,
        patch("app.services.scan_runner._fetch_certificate_der", return_value=self_signed_cert),
    ):
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://example.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is True
    assert result.certificate_status == "self_signed"
    assert any("auto-signé" in f for f in result.findings)
