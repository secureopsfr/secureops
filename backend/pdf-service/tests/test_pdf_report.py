"""Tests unitaires pour la génération PDF (app.services.pdf_report)."""

from app.services.pdf_report import generate_pdf
from app.services.pdf_report.findings import _group_findings_by_category
from app.services.pdf_report.pdf_i18n import t


def test_generate_pdf_returns_bytes() -> None:
    """generate_pdf retourne des bytes non vides."""
    pdf = generate_pdf(
        url="https://example.com",
        score=75,
        timestamp="2024-01-15T10:00:00Z",
        duration=5.2,
        findings=[
            {
                "id": "headers-csp-absent",
                "category": "headers",
                "title": "CSP absent",
                "severity": "medium",
                "evidence": "Header non présent",
                "recommendation": "Ajouter CSP",
                "references": ["https://developer.mozilla.org/docs/CSP"],
            },
        ],
        include_matrices=False,
        lang="fr",
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100
    assert pdf[:4] == b"%PDF"


def test_generate_pdf_en_lang() -> None:
    """generate_pdf avec lang=en produit un PDF valide."""
    pdf = generate_pdf(
        url="https://example.com",
        score=80,
        timestamp="2024-01-15T10:00:00Z",
        duration=3.0,
        findings=[],
        include_matrices=False,
        lang="en",
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100
    assert pdf[:4] == b"%PDF"


def test_group_findings_by_category() -> None:
    """_group_findings_by_category groupe correctement et préserve l'ordre."""
    findings = [
        {"id": "a", "category": "headers", "title": "H1"},
        {"id": "b", "category": "tls", "title": "T1"},
        {"id": "c", "category": "headers", "title": "H2"},
    ]
    by_cat, ordered = _group_findings_by_category(findings, "fr")
    assert "headers" in by_cat
    assert "tls" in by_cat
    assert len(by_cat["headers"]) == 2
    assert len(by_cat["tls"]) == 1
    assert ordered[0] == "tls"
    assert "headers" in ordered


def test_pdf_i18n_fr() -> None:
    """t() retourne la chaîne française pour lang=fr."""
    assert t("sommaire", "fr") == "Sommaire"
    assert t("score", "fr") == "Score"


def test_pdf_i18n_en() -> None:
    """t() retourne la chaîne anglaise pour lang=en."""
    assert t("sommaire", "en") == "Table of contents"
    assert t("score", "en") == "Score"


def test_report_pdf_endpoint(client) -> None:
    """POST /api/report/pdf retourne un PDF valide."""
    response = client.post(
        "/api/report/pdf",
        json={
            "url": "https://example.com",
            "score": 70,
            "timestamp": "2024-01-15T10:00:00Z",
            "duration": 4.0,
            "findings": [
                {
                    "id": "tls-https-disabled",
                    "category": "tls",
                    "title": "HTTPS désactivé",
                    "severity": "high",
                    "evidence": "Redirection HTTP",
                    "recommendation": "Activer HTTPS",
                    "references": [],
                },
            ],
        },
        params={"lang": "fr", "include_matrices": False},
    )
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    pdf = response.content
    assert len(pdf) > 500
    assert pdf[:4] == b"%PDF"
