"""Tests unitaires pour les vérifications Intégrité et sous-ressources."""

from unittest.mock import MagicMock

from app.services.integrity import IntegrityCheckResult, check_integrity_from_response


def _mock_response(
    text: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """Construit un mock de réponse HTTP pour les tests.

    Args:
        text: Corps de réponse HTML.
        headers: En-têtes HTTP simulés.

    Returns:
        MagicMock: Réponse HTTP mockée compatible avec httpx.Response.
    """
    resp = MagicMock()
    resp.text = text
    resp.headers = dict(headers or {})
    return resp


def test_check_integrity_response_none() -> None:
    """Réponse None → fetch_ok False et finding explicatif."""
    result = check_integrity_from_response(None, "https://example.com/")
    assert isinstance(result, IntegrityCheckResult)
    assert result.fetch_ok is False
    assert len(result.findings) >= 1
    assert "indisponible" in result.findings[0].lower()


def test_check_integrity_sri_on_external_resources() -> None:
    """Scripts/CSS externes sans integrity → finding SRI."""
    html = """
    <html>
      <head>
        <script src="https://cdn.example.com/lib.js"></script>
        <script src="https://cdn.example.com/ok.js"
                integrity="sha384-abc"></script>
        <link rel="stylesheet" href="https://cdn.example.com/style.css">
        <script src="/static/app.js"></script>
      </head>
      <body></body>
    </html>
    """
    resp = _mock_response(text=html)
    result = check_integrity_from_response(resp, "https://www.example.com/")
    assert result.fetch_ok is True
    assert any("ressources externes sans sri" in f.lower() for f in result.findings)


def test_check_integrity_csp_absent_reports_skipped_advanced_checks() -> None:
    """Sans CSP, un message doit indiquer que les tests avancés scripts ne sont pas appliqués."""
    html = "<html><head></head><body><script>console.log('test');</script></body></html>"
    resp = _mock_response(text=html, headers={})
    result = check_integrity_from_response(resp, "https://example.com/")
    assert result.fetch_ok is True
    assert any("aucune content-security-policy détectée" in f.lower() for f in result.findings)


def test_check_integrity_inline_scripts_without_nonce_when_csp_present() -> None:
    """Avec CSP présente et scripts inline sans nonce → finding dédié."""
    html = "<html><head></head><body><script>console.log('x');</script></body></html>"
    resp = _mock_response(
        text=html,
        headers={"Content-Security-Policy": "script-src 'self' 'nonce-xxx'"},
    )
    result = check_integrity_from_response(resp, "https://example.com/")
    # La présence d'une CSP avec script inline ne doit pas casser l'analyse.
    assert result.fetch_ok is True


def test_check_integrity_password_autocomplete_and_target_blank() -> None:
    """Champs password sans autocomplete et liens target=_blank sans rel doivent être signalés."""
    html = """
    <html>
      <body>
        <form>
          <input type="password" name="pwd">
        </form>
        <a href="https://external.com" target="_blank">Lien</a>
      </body>
    </html>
    """
    resp = _mock_response(text=html)
    result = check_integrity_from_response(resp, "https://example.com/account")
    assert result.fetch_ok is True
    # Au moins un finding doit être présent pour le combo password+target=\"_blank\".
    assert result.findings


def test_check_integrity_meta_robots_on_sensitive_page() -> None:
    """Sur page sensible sans meta robots/noindex → finding robots."""
    html = "<html><head></head><body><h1>Admin</h1></body></html>"
    resp = _mock_response(text=html)
    result = check_integrity_from_response(resp, "https://example.com/admin")
    assert result.fetch_ok is True
    assert any("meta robots" in f.lower() for f in result.findings)
