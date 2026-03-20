"""Tests unitaires pour les vérifications Tech Fingerprinting (passive)."""

from unittest.mock import MagicMock

from app.services.passive.both.tech_fingerprinting import TechFingerprintingCheckResult, check_tech_fingerprinting_from_response


def test_check_tech_fingerprinting_response_none() -> None:
    """Réponse None → fetch_ok False."""
    result = check_tech_fingerprinting_from_response(None)
    assert isinstance(result, TechFingerprintingCheckResult)
    assert result.fetch_ok is False
    assert result.server is None
    assert result.runtime is None
    assert result.framework_cms is None
    assert len(result.findings) >= 1


def test_check_tech_fingerprinting_server_and_x_powered_by() -> None:
    """Server et X-Powered-By présents → détection et extraction versions."""
    mock_resp = MagicMock()
    mock_resp.headers = {"Server": "nginx/1.24.0", "X-Powered-By": "PHP/8.2.0"}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.server == "nginx/1.24.0"
    assert result.server_version == "1.24.0"
    assert result.runtime == "PHP/8.2.0"
    assert result.runtime_version == "8.2.0"
    assert result.framework_cms == "PHP"
    assert "nginx" in str(result.findings).lower() or "Serveur" in str(result.findings)
    assert "PHP" in str(result.findings)
    assert len(result.stack_entries) >= 2


def test_check_tech_fingerprinting_express() -> None:
    """X-Powered-By: Express → framework Express."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Powered-By": "Express"}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "Express"
    assert "Express" in str(result.findings)


def test_check_tech_fingerprinting_drupal() -> None:
    """X-Drupal-Cache présent → Drupal."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Drupal-Cache": "HIT"}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "Drupal"


def test_check_tech_fingerprinting_wordpress() -> None:
    """X-Generator: WordPress → WordPress."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Generator": "WordPress 6.4"}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "WordPress"
    assert result.framework_cms_version == "6.4"


def test_check_tech_fingerprinting_stack_non_identifiee() -> None:
    """Aucun en-tête révélateur → stack non identifiée."""
    mock_resp = MagicMock()
    mock_resp.headers = {}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.server is None
    assert result.runtime is None
    assert result.framework_cms is None
    assert "non identifiée" in str(result.findings) or "masquée" in str(result.findings)


def test_check_tech_fingerprinting_html_meta_generator() -> None:
    """Meta generator WordPress dans HTML → détection."""
    mock_resp = MagicMock()
    mock_resp.headers = {}
    mock_resp.text = '<html><head><meta name="generator" content="WordPress 6.4.2"></head></html>'

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert any(e.product == "wordpress" for e in result.stack_entries)
    assert any(e.version == "6.4.2" for e in result.stack_entries)


def test_check_tech_fingerprinting_vulnerable_version() -> None:
    """Nginx 1.18.0 < 1.20.0 → version vulnérable détectée."""
    mock_resp = MagicMock()
    mock_resp.headers = {"Server": "nginx/1.18.0"}
    mock_resp.text = ""

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert len(result.vulnerable_versions) >= 1
    assert any(v.product == "nginx" and v.version == "1.18.0" for v in result.vulnerable_versions)


def test_tech_fingerprinting_check_result_to_dict() -> None:
    """to_dict() sérialise correctement."""
    result = TechFingerprintingCheckResult(
        server="nginx/1.24",
        server_version="1.24",
        runtime="PHP/8.2",
        runtime_version="8.2",
        framework_cms="WordPress",
        framework_cms_version=None,
        stack_entries=(),
        vulnerable_versions=(),
        findings=("Serveur détecté : nginx/1.24",),
        fetch_ok=True,
    )
    d = result.to_dict()

    assert d["server"] == "nginx/1.24"
    assert d["server_version"] == "1.24"
    assert d["runtime"] == "PHP/8.2"
    assert d["framework_cms"] == "WordPress"
    assert d["fetch_ok"] is True
    assert "findings" in d
    assert "stack_entries" in d
