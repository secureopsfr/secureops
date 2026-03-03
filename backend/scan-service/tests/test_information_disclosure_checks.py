"""Tests unitaires pour les vérifications Information disclosure (app.services.information_disclosure.checks)."""

from unittest.mock import MagicMock

from app.services.information_disclosure import InformationDisclosureCheckResult, check_information_disclosure_from_response


def _mock_response(
    content: bytes = b"",
    headers: dict | None = None,
    encoding: str = "utf-8",
) -> MagicMock:
    """Construit un mock de réponse HTTP pour les tests."""
    resp = MagicMock()
    resp.content = content
    resp.encoding = encoding
    resp.headers = dict(headers or {})
    return resp


def test_check_information_disclosure_response_none() -> None:
    """Réponse None → fetch_ok False et finding explicatif."""
    result = check_information_disclosure_from_response(None)
    assert isinstance(result, InformationDisclosureCheckResult)
    assert result.fetch_ok is False
    assert len(result.findings) >= 1
    assert "indisponible" in result.findings[0].lower() or "fuites" in result.findings[0].lower()


def test_check_information_disclosure_empty_response() -> None:
    """Réponse vide sans headers révélateurs → pas de findings (ou uniquement si connexion OK)."""
    resp = _mock_response(content=b"", headers={})
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert result.findings == ()


def test_check_information_disclosure_stack_trace_in_body() -> None:
    """Corps contenant une stack trace Python → finding stack trace."""
    body = b'Error\nTraceback (most recent call last):\n  File "main.py", line 42'
    resp = _mock_response(content=body, headers={})
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert any("stack trace" in f.lower() for f in result.findings)


def test_check_information_disclosure_debug_mode_in_body() -> None:
    """Corps contenant un message de mode développement → finding debug."""
    body = b"Development server is running at http://127.0.0.1:8000"
    resp = _mock_response(content=body, headers={})
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert any("debug" in f.lower() or "développement" in f.lower() for f in result.findings)


def test_check_information_disclosure_x_debug_header() -> None:
    """En-tête X-Debug-Token présent → finding headers de debug."""
    resp = _mock_response(content=b"<html></html>", headers={"X-Debug-Token": "abc123"})
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert any("debug" in f.lower() and "header" in f.lower() for f in result.findings)


def test_check_information_disclosure_server_version() -> None:
    """En-tête Server avec version → finding version serveur exposée."""
    resp = _mock_response(
        content=b"<html></html>",
        headers={"Server": "Apache/2.4.41"},
    )
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert any("server" in f.lower() and "version" in f.lower() for f in result.findings)


def test_check_information_disclosure_x_generator() -> None:
    """En-tête X-Generator présent → finding en-tête custom."""
    resp = _mock_response(
        content=b"<html></html>",
        headers={"X-Generator": "Drupal 10"},
    )
    result = check_information_disclosure_from_response(resp)
    assert result.fetch_ok is True
    assert any("custom" in f.lower() or "generator" in f.lower() for f in result.findings)
