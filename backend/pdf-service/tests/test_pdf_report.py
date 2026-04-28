"""Tests unitaires pour la génération PDF (app.services.pdf_report)."""

from app.schemas.finding import Finding
from app.services.pdf_report import generate_pdf
from app.services.pdf_report.constants import SEVERITY_LIST, severity_index
from app.services.pdf_report.cover import build_cover_page
from app.services.pdf_report.findings import _group_findings_by_category, _split_findings_by_type, build_category_sections, build_finding_block
from app.services.pdf_report.html_builder import build_html
from app.services.pdf_report.pdf_i18n import t
from app.services.pdf_report.sommaire import build_sommaire
from app.services.pdf_report.synthese import build_synthese

# ---------------------------------------------------------------------------
# Finding schema
# ---------------------------------------------------------------------------


def test_finding_default_values() -> None:
    """Finding accepte un dict vide et applique les valeurs par défaut."""
    f = Finding()
    assert f.id == ""
    assert f.category == "other"
    assert f.severity == "info"
    assert f.references == []


def test_finding_severity_normalised_lowercase() -> None:
    """Finding normalise la sévérité en minuscules."""
    f = Finding(severity="Critical")
    assert f.severity == "critical"
    f2 = Finding(severity="HIGH")
    assert f2.severity == "high"


def test_finding_severity_invalid_falls_back_to_info() -> None:
    """Une sévérité inconnue est remplacée par 'info'."""
    f = Finding(severity="unknown_level")
    assert f.severity == "info"


def test_finding_extra_fields_ignored() -> None:
    """Les champs inconnus du scan-service sont ignorés sans erreur."""
    f = Finding(**{"id": "x", "extra_field": "ignored"})
    assert f.id == "x"
    assert not hasattr(f, "extra_field")


# ---------------------------------------------------------------------------
# Constantes de sévérité
# ---------------------------------------------------------------------------


def test_severity_order_is_complete() -> None:
    """SEVERITY_LIST couvre les 5 niveaux attendus."""
    assert SEVERITY_LIST == ["critical", "high", "medium", "low", "info"]


def test_severity_index_ordering() -> None:
    """Index de tri : critical < high < medium < low < info."""
    assert severity_index("critical") < severity_index("high")
    assert severity_index("high") < severity_index("medium")
    assert severity_index("medium") < severity_index("low")
    assert severity_index("low") < severity_index("info")


def test_severity_index_unknown_returns_99() -> None:
    """Sévérité inconnue retourne 99 (trié en dernier)."""
    assert severity_index("unknown") == 99


# ---------------------------------------------------------------------------
# Troncature avec ellipse
# ---------------------------------------------------------------------------


def test_build_finding_block_truncates_long_evidence() -> None:
    """Une evidence > evidence_max_len est tronquée avec '…' dans le HTML."""
    long_evidence = "A" * 1000
    f = Finding(id="", category="headers", severity="medium", evidence=long_evidence)
    html = build_finding_block(f, section_num=2, finding_idx=2, include_matrices=False, lang="fr")
    assert "…" in html
    assert "A" * 1000 not in html


def test_build_finding_block_short_evidence_not_truncated() -> None:
    """Une evidence courte n'est pas tronquée."""
    f = Finding(id="", category="headers", severity="medium", evidence="Texte court")
    html = build_finding_block(f, section_num=2, finding_idx=2, include_matrices=False, lang="fr")
    assert "Texte court" in html
    assert "…" not in html


# ---------------------------------------------------------------------------
# Échappement HTML
# ---------------------------------------------------------------------------


def test_build_cover_page_escapes_url() -> None:
    """Les caractères HTML dans l'URL sont échappés dans la page de garde."""
    html = build_cover_page(
        url="https://example.com/<script>alert(1)</script>",
        date_str="2026-01-01 10:00",
        lang="fr",
        report_title="Rapport",
        subtitle="SecureOps",
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html  # noqa: Q000


def test_build_finding_block_escapes_title() -> None:
    """Les balises HTML dans le titre d'un finding sont échappées."""
    f = Finding(id="", title="<b>injection</b>", severity="low", category="headers")
    html = build_finding_block(f, section_num=2, finding_idx=2, include_matrices=False, lang="fr")
    assert "<b>injection</b>" not in html
    assert "&lt;b&gt;injection&lt;/b&gt;" in html  # noqa: Q000


def test_build_finding_block_uses_english_catalog_evidence() -> None:
    """Le rapport anglais ne reprend pas l'evidence française du scan si le catalogue traduit existe."""
    f = Finding(
        id="headers-csp-no-report-uri",
        category="headers",
        severity="low",
        evidence="CSP présent mais sans report-uri ni report-to : violations non détectables.",
    )
    html = build_finding_block(f, section_num=2, finding_idx=2, include_matrices=False, lang="en")
    assert "CSP present but missing report-uri or report-to" in html
    assert "CSP présent" not in html


def test_build_finding_block_hides_french_evidence_when_english_catalog_missing() -> None:
    """Le rapport anglais utilise un fallback EN pour les slugs connus sans evidence_en."""
    f = Finding(
        id="tls-no-redirect",
        category="tls",
        severity="high",
        evidence="Detected on 2 page(s): https://example.com, https://example.com/login\nPas de redirection HTTP→HTTPS détectée.",
    )
    html = build_finding_block(f, section_num=2, finding_idx=2, include_matrices=False, lang="en")
    assert "Detected on 2 page(s)" in html
    assert "Finding detected during the scan: No HTTP→HTTPS redirect." in html
    assert "Pas de redirection" not in html


# ---------------------------------------------------------------------------
# Groupement et tri
# ---------------------------------------------------------------------------


def test_group_findings_by_category() -> None:
    """_group_findings_by_category groupe correctement et préserve l'ordre."""
    findings = [
        Finding(id="a", category="headers", title="H1"),
        Finding(id="b", category="tls", title="T1"),
        Finding(id="c", category="headers", title="H2"),
    ]
    by_cat, ordered = _group_findings_by_category(findings, "fr")
    assert "headers" in by_cat
    assert "tls" in by_cat
    assert len(by_cat["headers"]) == 2
    assert len(by_cat["tls"]) == 1
    assert ordered[0] == "tls"
    assert "headers" in ordered


def test_group_findings_empty() -> None:
    """_group_findings_by_category ne plante pas avec une liste vide."""
    by_cat, ordered = _group_findings_by_category([], "fr")
    assert by_cat == {}
    assert isinstance(ordered, list)


def test_split_findings_by_type_separates_info() -> None:
    """Les findings info sont séparés des anomalies pour le rendu PDF."""
    findings = [
        Finding(id="a", category="headers", title="Anomalie", severity="medium"),
        Finding(id="b", category="headers", title="Info", severity="info"),
    ]
    anomalies, infos = _split_findings_by_type(findings)
    assert [f.title for f in anomalies] == ["Anomalie"]
    assert [f.title for f in infos] == ["Info"]


# ---------------------------------------------------------------------------
# Builders HTML
# ---------------------------------------------------------------------------


def test_build_cover_page_contains_url() -> None:
    """La page de garde contient l'URL scannée."""
    html = build_cover_page("https://example.com", "01/01/2026 10:00", "fr", "Rapport", "Sous-titre")
    assert "example.com" in html
    assert "cover-page" in html


def test_build_sommaire_with_findings() -> None:
    """Le sommaire liste les catégories ayant des findings."""
    findings = [Finding(id="x", category="headers", title="CSP absent", severity="medium")]
    by_cat, ordered = _group_findings_by_category(findings, "fr")
    html = build_sommaire(by_cat, ordered, "fr")
    assert "toc-list" in html
    assert "En-têtes de sécurité" in html


def test_build_sommaire_empty_findings() -> None:
    """Le sommaire se génère sans erreur même sans findings."""
    html = build_sommaire({}, [], "fr")
    assert "toc-list" in html
    assert "Synthèse" in html or "synthese" in html.lower()


def test_build_synthese_score_gauge() -> None:
    """La section synthèse inclut le score dans la jauge SVG."""
    findings = [Finding(id="a", category="tls", severity="high")]
    by_cat, ordered = _group_findings_by_category(findings, "fr")
    html = build_synthese(by_cat, ordered, findings, score_val=72, score_color="#f59e0b", lang="fr")
    assert "72" in html
    assert "synthese-gauge" in html


def test_build_synthese_counts_anomalies_without_infos() -> None:
    """Le compteur de synthèse PDF compte seulement les anomalies."""
    findings = [
        Finding(id="a", category="tls", title="TLS faible", severity="high"),
        Finding(id="b", category="tls", title="Version détectée", severity="info"),
    ]
    anomalies, infos = _split_findings_by_type(findings)
    by_cat, ordered = _group_findings_by_category(anomalies, "fr")
    info_by_cat, _ = _group_findings_by_category(infos, "fr")
    html = build_synthese(by_cat, ordered, anomalies, score_val=72, score_color="#f59e0b", lang="fr", info_by_category=info_by_cat)
    assert '<span class="synthese-anomalies-value">1</span>' in html
    assert "synthese-info-value" not in html
    assert "1 info" in html


def test_build_category_sections_renders_infos_in_category() -> None:
    """Les infos sont rendues dans leur catégorie, sans section dédiée."""
    info_findings = [Finding(id="", category="headers", title="Technologie détectée", severity="info")]
    info_by_cat, _ = _group_findings_by_category(info_findings, "fr")
    sections, next_section = build_category_sections({}, [], include_matrices=False, lang="fr", info_by_category=info_by_cat)
    html = "".join(sections)
    assert next_section == 3
    assert 'id="sect-headers"' in html
    assert 'id="sect-infos"' not in html
    assert "Technologie détectée" in html


def test_build_synthese_multi_ignores_info_findings_in_counts() -> None:
    """Le tableau multi-pages ne compte pas les infos comme anomalies."""
    html = build_synthese(
        by_category={},
        ordered_cats=[],
        findings=[],
        score_val=80,
        score_color="#10b981",
        lang="fr",
        base_url="https://example.com",
        result_mode="multi",
        page_results=[
            {
                "url": "https://example.com/a",
                "score": 80,
                "findings": [{"category": "headers", "severity": "info", "title": "Technologie détectée"}],
                "category_summaries": [{"category": "headers", "anomaly_count": 1, "checks_count": 1}],
            }
        ],
    )
    assert "anomaly-chip" not in html
    assert "info-chip" in html


def test_build_html_returns_full_document() -> None:
    """build_html retourne un document HTML complet avec doctype."""
    findings = [Finding(id="headers-csp-absent", category="headers", severity="medium")]
    html = build_html(
        url="https://example.com",
        score=65,
        timestamp="2026-01-15T10:00:00Z",
        duration=3.0,
        findings=findings,
        include_matrices=False,
        lang="fr",
    )
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "example.com" in html


def test_build_html_separates_infos_from_anomalies() -> None:
    """Le rapport complet ne mélange pas infos et anomalies."""
    findings = [
        Finding(id="", category="headers", title="Header manquant", severity="medium"),
        Finding(id="", category="headers", title="Technologie détectée", severity="info"),
    ]
    html = build_html(
        url="https://example.com",
        score=65,
        timestamp="2026-01-15T10:00:00Z",
        duration=3.0,
        findings=findings,
        include_matrices=False,
        lang="fr",
    )
    assert '<span class="synthese-anomalies-value">1</span>' in html
    assert 'id="sect-infos"' not in html
    assert 'id="sect-headers"' in html
    assert "Technologie détectée" in html


# ---------------------------------------------------------------------------
# generate_pdf (intégration WeasyPrint)
# ---------------------------------------------------------------------------


def test_generate_pdf_returns_bytes() -> None:
    """generate_pdf retourne des bytes non vides commençant par %PDF."""
    pdf = generate_pdf(
        url="https://example.com",
        score=75,
        timestamp="2024-01-15T10:00:00Z",
        duration=5.2,
        findings=[
            Finding(
                id="headers-csp-absent",
                category="headers",
                title="CSP absent",
                severity="medium",
                evidence="Header non présent",
                recommendation="Ajouter CSP",
                references=["https://developer.mozilla.org/docs/CSP"],
            ),
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


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------


def test_pdf_i18n_fr() -> None:
    """t() retourne la chaîne française pour lang=fr."""
    assert t("sommaire", "fr") == "Sommaire"
    assert t("score", "fr") == "Score"


def test_pdf_i18n_en() -> None:
    """t() retourne la chaîne anglaise pour lang=en."""
    assert t("sommaire", "en") == "Table of contents"
    assert t("score", "en") == "Score"


# ---------------------------------------------------------------------------
# Endpoint HTTP
# ---------------------------------------------------------------------------


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


def test_report_pdf_endpoint_normalises_severity(client) -> None:
    """Le endpoint accepte une sévérité en majuscules et la normalise."""
    response = client.post(
        "/api/report/pdf",
        json={
            "url": "https://example.com",
            "score": 50,
            "timestamp": "2024-01-15T10:00:00Z",
            "duration": 2.0,
            "findings": [
                {"id": "", "category": "headers", "title": "Test", "severity": "MEDIUM"},
            ],
        },
        params={"lang": "fr", "include_matrices": False},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_report_pdf_endpoint_ignores_unknown_finding_fields(client) -> None:
    """Les champs inconnus dans les findings sont ignorés sans erreur 422."""
    response = client.post(
        "/api/report/pdf",
        json={
            "url": "https://example.com",
            "score": 60,
            "timestamp": "2024-01-15T10:00:00Z",
            "duration": 1.0,
            "findings": [
                {
                    "id": "tls-https-disabled",
                    "category": "tls",
                    "severity": "high",
                    "unknown_field": "should_be_ignored",
                    "another_unknown": 42,
                },
            ],
        },
        params={"lang": "fr", "include_matrices": False},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
