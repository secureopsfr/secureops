"""Tests unitaires pour les vérifications Tech Fingerprinting (app.services.tech_fingerprinting.checks)."""

from unittest.mock import MagicMock

from app.services.tech_fingerprinting import (
    TechFingerprintingCheckResult,
    check_tech_fingerprinting_from_response,
)


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
    """Server et X-Powered-By présents → détection."""
    mock_resp = MagicMock()
    mock_resp.headers = {"Server": "nginx/1.24.0", "X-Powered-By": "PHP/8.2.0"}

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.server == "nginx/1.24.0"
    assert result.runtime == "PHP/8.2.0"
    assert result.framework_cms == "PHP"
    assert "nginx" in str(result.findings).lower() or "Serveur" in str(result.findings)
    assert "PHP" in str(result.findings)


def test_check_tech_fingerprinting_express() -> None:
    """X-Powered-By: Express → framework Express."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Powered-By": "Express"}

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "Express"
    assert "Express" in str(result.findings)


def test_check_tech_fingerprinting_drupal() -> None:
    """X-Drupal-Cache présent → Drupal."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Drupal-Cache": "HIT"}

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "Drupal"


def test_check_tech_fingerprinting_wordpress() -> None:
    """X-Generator: WordPress → WordPress."""
    mock_resp = MagicMock()
    mock_resp.headers = {"X-Generator": "WordPress 6.4"}

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.framework_cms == "WordPress"


def test_check_tech_fingerprinting_stack_non_identifiee() -> None:
    """Aucun en-tête révélateur → stack non identifiée."""
    mock_resp = MagicMock()
    mock_resp.headers = {}

    result = check_tech_fingerprinting_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.server is None
    assert result.runtime is None
    assert result.framework_cms is None
    assert "non identifiée" in str(result.findings) or "masquée" in str(result.findings)


def test_tech_fingerprinting_check_result_to_dict() -> None:
    """to_dict() sérialise correctement."""
    result = TechFingerprintingCheckResult(
        server="nginx/1.24",
        runtime="PHP/8.2",
        framework_cms="WordPress",
        findings=("Serveur détecté : nginx/1.24",),
        fetch_ok=True,
    )
    d = result.to_dict()

    assert d["server"] == "nginx/1.24"
    assert d["runtime"] == "PHP/8.2"
    assert d["framework_cms"] == "WordPress"
    assert d["fetch_ok"] is True
    assert "findings" in d
