"""Tests unitaires pour le scoring (app.services.scoring)."""

from app.models.finding import Finding
from app.services.scoring import compute_score


def _finding(category: str, severity: str, slug: str = "test") -> Finding:
    """Helper pour créer un Finding minimal pour les tests de scoring."""
    return Finding(
        id=slug,
        category=category,
        title="Test",
        severity=severity,
        evidence="",
        recommendation="",
        references=(),
    )


def test_compute_score_empty_findings() -> None:
    """compute_score avec findings vides retourne 100."""
    assert compute_score(()) == 100


def test_compute_score_single_critical() -> None:
    """Un finding critical réduit le score."""
    findings = (_finding("tls", "critical"),)
    score = compute_score(findings)
    assert score < 100
    assert 0 <= score <= 100


def test_compute_score_single_info_no_penalty() -> None:
    """Un finding info (pénalité 0) ne réduit pas le score de la catégorie."""
    findings = (_finding("tech_fingerprinting", "info"),)
    score = compute_score(findings)
    assert score == 100


def test_compute_score_single_high_tls() -> None:
    """Un finding high dans TLS (poids 25) réduit le score proportionnellement."""
    findings = (_finding("tls", "high"),)
    score = compute_score(findings)
    # TLS poids 25, high pénalité 50 → cat_score = 50, contribution = 12.5 ; autres catégories = 100
    assert 85 <= score <= 95
    assert score < 100


def test_compute_score_multiple_categories() -> None:
    """Plusieurs findings dans différentes catégories appliquent la pondération."""
    findings = (
        _finding("tls", "high"),
        _finding("headers", "medium"),
    )
    score = compute_score(findings)
    assert score < 100
    assert 0 <= score <= 100


def test_compute_score_all_critical() -> None:
    """Tous les findings critical donnent un score de 0."""
    findings = (
        _finding("tls", "critical"),
        _finding("headers", "critical"),
        _finding("cookies", "critical"),
        _finding("exposed_files", "critical"),
        _finding("directory_listing", "critical"),
        _finding("robots_txt", "critical"),
        _finding("sitemap", "critical"),
        _finding("tech_fingerprinting", "critical"),
    )
    score = compute_score(findings)
    assert score == 0


def test_compute_score_one_medium_header() -> None:
    """Un seul finding medium dans headers (poids 25) : score partiel."""
    findings = (_finding("headers", "medium"),)
    score = compute_score(findings)
    # headers cat_score = 75, contribution = 18.75 ; autres catégories = 100 → total ≈ 99
    assert score < 100
    assert 95 <= score <= 100


def test_compute_score_severity_lowercase() -> None:
    """compute_score accepte les sévérités en minuscules."""
    findings = (_finding("tls", "critical"),)
    score = compute_score(findings)
    assert score < 100


def test_compute_score_exposure_category() -> None:
    """exposed_files et directory_listing contribuent au score (Exposure 20)."""
    findings = (
        _finding("exposed_files", "critical"),
        _finding("directory_listing", "high"),
    )
    score = compute_score(findings)
    assert score < 100
    assert 0 <= score <= 100


def test_compute_score_rounds_to_int() -> None:
    """compute_score retourne un entier."""
    findings = (_finding("tls", "high"),)
    score = compute_score(findings)
    assert isinstance(score, int)


def test_compute_score_bounded_0_100() -> None:
    """compute_score est toujours entre 0 et 100."""
    findings = tuple(_finding("tls", "critical") for _ in range(20))
    score = compute_score(findings)
    assert 0 <= score <= 100
