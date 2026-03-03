"""Tests unitaires pour les vérifications Security Headers (app.services.security_headers.checks)."""

from unittest.mock import MagicMock

from app.services.security_headers import check_security_headers_from_response


def test_check_security_headers_tous_presents() -> None:
    """check_security_headers_from_response retourne tous les headers présents si la réponse les contient."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "Content-Security-Policy": "default-src 'self'; report-uri /csp-report",
        "Strict-Transport-Security": "max-age=31536000",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=()",
        "Cross-Origin-Embedder-Policy": "credentialless",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Clear-Site-Data": '"cookies"',
    }

    result = check_security_headers_from_response(mock_resp)

    assert result.fetch_ok is True
    assert len(result.headers_present) == 9
    assert "Content-Security-Policy" in result.headers_present
    assert "Cross-Origin-Embedder-Policy" in result.headers_present
    assert result.headers_missing == ()
    assert result.findings == ()


def test_check_security_headers_aucun_present() -> None:
    """check_security_headers_from_response détecte tous les headers manquants."""
    mock_resp = MagicMock()
    mock_resp.headers = {}

    result = check_security_headers_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.headers_present == ()
    assert len(result.headers_missing) == 9
    assert len(result.findings) == 9
    assert any("Content-Security-Policy" in f for f in result.findings)
    assert any("XSS" in f for f in result.findings)
    assert any("X-Frame-Options" in f for f in result.findings)


def test_check_security_headers_x_content_type_options_mauvais() -> None:
    """check_security_headers_from_response détecte X-Content-Type-Options avec valeur incorrecte."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "X-Content-Type-Options": "invalid",
    }

    result = check_security_headers_from_response(mock_resp)

    assert result.fetch_ok is True
    assert "X-Content-Type-Options" in result.headers_present
    assert any("nosniff" in f for f in result.findings)
    assert any("valeur incorrecte" in f for f in result.findings)


def test_check_security_headers_response_none() -> None:
    """check_security_headers_from_response retourne fetch_ok=False quand response est None."""
    result = check_security_headers_from_response(None)

    assert result.fetch_ok is False
    assert result.headers_present == ()
    assert len(result.headers_missing) == 9
    assert len(result.findings) == 1
    assert "en-têtes" in result.findings[0].lower()


def test_check_security_headers_headers_case_insensitive() -> None:
    """Les noms d'en-têtes HTTP sont insensibles à la casse."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "content-security-policy": "default-src 'self'; report-uri /csp",
        "x-frame-options": "DENY",
    }

    result = check_security_headers_from_response(mock_resp)

    assert result.fetch_ok is True
    assert "Content-Security-Policy" in result.headers_present
    assert "X-Frame-Options" in result.headers_present
    assert len(result.headers_missing) == 7
    assert len(result.findings) == 7
    assert not any("violations non détectables" in f for f in result.findings)
    assert not any("unsafe-inline" in f or "unsafe-eval" in f for f in result.findings)


def test_check_security_headers_csp_sans_report_uri() -> None:
    """CSP présent sans report-uri ni report-to génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "Content-Security-Policy": "default-src 'self'; script-src 'self'",
    }

    result = check_security_headers_from_response(mock_resp)

    assert result.fetch_ok is True
    assert "Content-Security-Policy" in result.headers_present
    assert any("report-uri" in f and "report-to" in f for f in result.findings)
    assert any("violations non détectables" in f for f in result.findings)


def test_check_security_headers_csp_avec_report_uri() -> None:
    """CSP avec report-uri ne génère pas de finding report-uri."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "Content-Security-Policy": "default-src 'self'; report-uri /csp-report",
    }

    result = check_security_headers_from_response(mock_resp)

    assert "Content-Security-Policy" in result.headers_present
    assert not any("violations non détectables" in f for f in result.findings)


def test_check_security_headers_csp_unsafe_directives() -> None:
    """CSP avec unsafe-inline ou unsafe-eval génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
    }

    result = check_security_headers_from_response(mock_resp)

    assert "Content-Security-Policy" in result.headers_present
    assert any("unsafe-inline" in f or "unsafe-eval" in f for f in result.findings)
    assert any("risque XSS accru" in f for f in result.findings)


def test_check_security_headers_csp_unsafe_eval() -> None:
    """CSP avec unsafe-eval génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers = {
        "Content-Security-Policy": "script-src 'unsafe-eval'",
    }

    result = check_security_headers_from_response(mock_resp)

    assert any("unsafe-eval" in f for f in result.findings)
