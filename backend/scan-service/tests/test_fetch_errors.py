"""Tests du module de gestion des erreurs de fetch (app/errors/fetch_errors)."""

import httpx

from app.errors.fetch_errors import (
    ERROR_TYPE_CONNECTION_FAILED,
    ERROR_TYPE_TIMEOUT,
    ERROR_TYPE_TLS_ERROR,
    ERROR_TYPE_UNKNOWN,
    MSG_SITE_INACCESSIBLE,
    MSG_TIMEOUT,
    MSG_TLS_ERROR,
    MSG_TLS_OPENSSL_LEGACY,
    FetchResult,
    build_sse_error_payload,
    classify_fetch_exception,
)


def test_classify_connect_error() -> None:
    """Vérifie que ConnectError produit connection_failed et 503."""
    exc = httpx.ConnectError("Connection refused")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.response is None
    assert result.error_type == ERROR_TYPE_CONNECTION_FAILED
    assert result.message == MSG_SITE_INACCESSIBLE
    assert result.status_code == 503


def test_classify_connect_timeout() -> None:
    """Vérifie que ConnectTimeout produit timeout et 504."""
    exc = httpx.ConnectTimeout("Connection timed out")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.error_type == ERROR_TYPE_TIMEOUT
    assert result.message == MSG_TIMEOUT
    assert result.status_code == 504


def test_classify_read_timeout() -> None:
    """Vérifie que ReadTimeout produit timeout et 504."""
    exc = httpx.ReadTimeout("Read timed out")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.error_type == ERROR_TYPE_TIMEOUT
    assert result.status_code == 504


def test_classify_tls_openssl_legacy() -> None:
    """Exception no_protocols_available → tls_error, message OpenSSL 3.x."""
    exc = Exception("no_protocols_available: TLS 1.0/1.1 disabled")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.error_type == ERROR_TYPE_TLS_ERROR
    assert result.message == MSG_TLS_OPENSSL_LEGACY
    assert result.status_code == 502


def test_classify_tls_ssl_error() -> None:
    """Exception SSL → tls_error."""
    exc = Exception("SSL handshake failed: certificate verify failed")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.error_type == ERROR_TYPE_TLS_ERROR
    assert result.message == MSG_TLS_ERROR
    assert result.status_code == 502


def test_classify_unknown_error() -> None:
    """Exception inconnue → unknown, 500."""
    exc = Exception("Something went wrong")
    result = classify_fetch_exception(exc)
    assert result.success is False
    assert result.error_type == ERROR_TYPE_UNKNOWN
    assert result.status_code == 500


def test_build_sse_error_payload() -> None:
    """build_sse_error_payload produit un dict avec message, status_code, error_type."""
    result = FetchResult(
        success=False,
        response=None,
        error_type=ERROR_TYPE_CONNECTION_FAILED,
        message=MSG_SITE_INACCESSIBLE,
        status_code=503,
        details="Connection refused",
    )
    payload = build_sse_error_payload(result)
    assert payload["message"] == MSG_SITE_INACCESSIBLE
    assert payload["status_code"] == 503
    assert payload["error_type"] == ERROR_TYPE_CONNECTION_FAILED
    assert "details" not in payload


def test_build_sse_error_payload_include_details() -> None:
    """build_sse_error_payload avec include_details=True inclut details."""
    result = FetchResult(
        success=False,
        response=None,
        error_type=ERROR_TYPE_CONNECTION_FAILED,
        message=MSG_SITE_INACCESSIBLE,
        status_code=503,
        details="Connection refused",
    )
    payload = build_sse_error_payload(result, include_details=True)
    assert payload["details"] == "Connection refused"


def test_build_timeout_global_error_payload() -> None:
    """build_timeout_global_error_payload retourne payload 408."""
    from app.errors.fetch_errors import build_timeout_global_error_payload

    payload = build_timeout_global_error_payload()
    assert payload["message"] == "Délai global du scan dépassé."
    assert payload["status_code"] == 408
    assert payload["error_type"] == "timeout_global"


def test_build_validation_error_payload() -> None:
    """build_validation_error_payload retourne payload 400."""
    from app.errors.fetch_errors import build_validation_error_payload

    payload = build_validation_error_payload("URL invalide")
    assert payload["message"] == "URL invalide"
    assert payload["status_code"] == 400
    assert payload["error_type"] == "validation_error"


def test_build_unexpected_error_payload() -> None:
    """build_unexpected_error_payload retourne payload 500."""
    from app.errors.fetch_errors import build_unexpected_error_payload

    payload = build_unexpected_error_payload("Connection reset")
    assert "Connection reset" in payload["message"]
    assert payload["status_code"] == 500
    assert payload["error_type"] == "unknown"
