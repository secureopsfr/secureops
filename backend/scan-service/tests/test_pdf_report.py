"""Tests unitaires pour la génération PDF (app.services.pdf_report)."""

import pytest

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
    assert "tls" in ordered
    assert "headers" in ordered


def test_pdf_i18n_fr() -> None:
    """t() retourne le français pour lang=fr."""
    assert t("sommaire", "fr") == "Sommaire"
    assert t("evidence", "fr") == "Preuve"
    assert t("how_to_fix", "fr") == "Comment corriger"


def test_pdf_i18n_en() -> None:
    """t() retourne l'anglais pour lang=en."""
    assert t("sommaire", "en") == "Table of contents"
    assert t("evidence", "en") == "Evidence"
    assert t("how_to_fix", "en") == "How to fix"


def test_pdf_i18n_fallback_fr() -> None:
    """t() avec lang invalide retombe sur fr."""
    assert t("sommaire", "de") == "Sommaire"
    assert t("sommaire", "") == "Sommaire"


def test_generate_pdf_tech_fingerprinting_en() -> None:
    """PDF en anglais : tech_fingerprinting-stack-unknown affiche titres/détails en EN."""
    from app.services.pdf_report.findings import build_finding_block

    finding = {
        "id": "tech_fingerprinting-stack-unknown",
        "category": "tech_fingerprinting",
        "title": "Stack non identifiée",
        "severity": "info",
        "evidence": "Stack : non identifiée (ou masquée)",
        "recommendation": "Information : stack non identifiée ou masquée. Pas d'action requise.",
        "references": [],
    }
    html = build_finding_block(finding, section_num=3, finding_idx=1, include_matrices=False, lang="en")
    assert "Stack not identified" in html
    assert "Evidence" in html
    assert "Detail" in html
    assert "No revealing header" in html or "intentionally hidden" in html
    assert "Stack non identifiée" not in html


def test_generate_pdf_headers_referrer_en() -> None:
    """PDF en anglais : headers-referrer-absent affiche tout en EN."""
    from app.services.pdf_report.findings import build_finding_block

    finding = {
        "id": "headers-referrer-absent",
        "category": "headers",
        "title": "Referrer-Policy absent",
        "severity": "medium",
        "evidence": "Referrer-Policy absent : risque de fuite d'URLs sensibles.",
        "recommendation": "Ajouter Referrer-Policy...",
        "references": ["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy"],
    }
    html = build_finding_block(finding, section_num=2, finding_idx=1, include_matrices=False, lang="en")
    assert "Evidence" in html
    assert "Detail" in html
    assert "risk of sensitive URL leakage" in html
    assert "Add Referrer-Policy" in html
    assert "risque de fuite" not in html


def test_generate_pdf_exposed_files_en() -> None:
    """PDF en anglais : exposed_files-env affiche titre/evidence/recommendation en EN."""
    from app.services.pdf_report.findings import build_finding_block

    finding = {
        "id": "exposed_files-env",
        "category": "exposed_files",
        "title": "Fichier .env exposé",
        "severity": "critical",
        "evidence": "Fichier .env exposé : credentials et secrets accessibles.",
        "recommendation": "Bloquer l'accès...",
        "references": [],
    }
    html = build_finding_block(finding, section_num=4, finding_idx=1, include_matrices=False, lang="en")
    assert "File .env exposed" in html
    assert "credentials and secrets accessible" in html
    assert "Block access" in html
    assert "Fichier .env exposé" not in html


@pytest.mark.integration()
def test_pdf_integration_scan_to_pdf(client) -> None:
    """Test d'intégration : scan complet → génération PDF bout en bout.

    Lance un scan mocké (headers manquants), récupère le result, génère le PDF.
    Exclure en CI avec : pytest -m 'not integration'
    """
    from tests.conftest import parse_sse_events, patch_scan_checks

    with patch_scan_checks():
        response = client.post("/api/scan", json={"url": "https://example.com"})

    assert response.status_code == 200
    events = parse_sse_events(response)
    result_events = [e for e in events if e[0] == "result"]
    assert len(result_events) == 1, "Scan doit produire un événement result"

    data = result_events[0][1]
    pdf = generate_pdf(
        url=data["url"],
        score=data["score"],
        timestamp=data["timestamp"],
        duration=data["duration"],
        findings=data["findings"],
        include_matrices=True,
        lang="en",
    )

    assert isinstance(pdf, bytes)
    assert len(pdf) > 500
    assert pdf[:4] == b"%PDF"
    # Le scan mocké a headers vides → findings headers manquants
    assert len(data["findings"]) > 0
