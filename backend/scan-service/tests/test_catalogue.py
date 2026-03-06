"""Tests unitaires pour le catalogue des recommandations (app.catalogue)."""

from app.catalogue.recommendations import get_detail, get_evidence, get_recommendation, get_references, get_title


def test_get_recommendation_known_slug() -> None:
    """get_recommendation retourne le texte pour un slug connu."""
    rec = get_recommendation("tls-https-disabled")
    assert rec
    assert "HTTPS" in rec


def test_get_recommendation_unknown_slug() -> None:
    """get_recommendation retourne un message générique pour un slug inconnu."""
    rec = get_recommendation("slug-inexistant-xyz")
    assert "documentation" in rec.lower() or "sécurité" in rec.lower()


def test_get_recommendation_unknown_slug_en() -> None:
    """get_recommendation(slug, en) retourne le message générique en anglais."""
    rec = get_recommendation("slug-inexistant-xyz", "en")
    assert "consult" in rec.lower() or "security" in rec.lower()


def test_get_references_known_slug() -> None:
    """get_references retourne les URLs pour un slug connu."""
    refs = get_references("tls-https-disabled")
    assert isinstance(refs, tuple)
    assert len(refs) >= 1
    assert refs[0].startswith("https://")


def test_get_references_unknown_slug() -> None:
    """get_references retourne tuple vide pour un slug inconnu."""
    refs = get_references("slug-inexistant-xyz")
    assert refs == ()


def test_get_references_headers_csp_has_multiple() -> None:
    """headers-csp-absent a plusieurs références."""
    refs = get_references("headers-csp-absent")
    assert len(refs) >= 2


def test_get_recommendation_headers_csp() -> None:
    """get_recommendation pour headers-csp-absent contient CSP ou Content-Security."""
    rec = get_recommendation("headers-csp-absent")
    assert "Content-Security" in rec or "CSP" in rec or "XSS" in rec


def test_get_recommendation_i18n_en() -> None:
    """get_recommendation(slug, lang=en) retourne l'anglais pour tech_fingerprinting-stack-unknown."""
    rec = get_recommendation("tech_fingerprinting-stack-unknown", "en")
    assert "stack not identified" in rec.lower() or "no action required" in rec.lower()


def test_get_title_evidence_i18n() -> None:
    """get_title et get_evidence retournent les traductions pour tech_fingerprinting-stack-unknown."""
    assert get_title("tech_fingerprinting-stack-unknown", "fr") == "Stack non identifiée"
    assert get_title("tech_fingerprinting-stack-unknown", "en") == "Stack not identified"
    assert "non identifiée" in get_evidence("tech_fingerprinting-stack-unknown", "fr")
    assert "not identified" in get_evidence("tech_fingerprinting-stack-unknown", "en")


def test_get_detail_i18n() -> None:
    """get_detail retourne detail_fr ou detail_en selon lang."""
    fr = get_detail("tech_fingerprinting-stack-unknown", "fr")
    en = get_detail("tech_fingerprinting-stack-unknown", "en")
    assert "Aucun en-tête" in fr or "masquée" in fr
    assert "No revealing header" in en or "intentionally hidden" in en
