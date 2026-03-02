"""Section Synthèse du rapport PDF."""

from html import escape
from typing import Any

from app.config.pdf import get_category_labels, get_pdf_settings
from app.services.pdf_report.pdf_i18n import t


def build_synthese(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    findings: list[dict[str, Any]],
    score_val: int,
    score_color: str,
    lang: str,
) -> str:
    """Construit le HTML de la section Synthèse.

    Args:
        by_category: Findings groupés par catégorie.
        ordered_cats: Ordre des catégories.
        findings: Liste des findings.
        score_val: Score /100.
        score_color: Couleur du score.
        lang: Code langue (fr/en).

    Returns:
        str: HTML de la synthèse.
    """
    synthese_label = t("synthese", lang)
    score_synthese = t("score", lang)
    tests_label = t("tests_performed", lang)
    test_label = t("test", lang)
    status_label = t("status", lang)
    status_ok = t("status_ok", lang)
    anomalies_word = t("anomalies", lang)
    repartition_label = t("repartition", lang)
    cat_label = t("category", lang)
    nb_label = t("count", lang)
    anomalies_label = t("anomalies_detected", lang)

    settings = get_pdf_settings()
    checked_cats = settings.categories.checked
    category_labels = get_category_labels(lang)

    test_rows = []
    for cat in checked_cats:
        count = len(by_category.get(cat, []))
        label = category_labels.get(cat, cat)
        if count == 0:
            status_html = f'<span class="status-ok">{status_ok}</span>'
        else:
            status_html = f'<span class="status-fail">{count} {anomalies_word}</span>'
        test_rows.append(f"<tr><td>{escape(label)}</td><td>{status_html}</td></tr>")

    synthese_rows = []
    for cat in ordered_cats:
        count = len(by_category.get(cat, []))
        if count > 0:
            label = category_labels.get(cat, cat)
            synthese_rows.append(f"<tr><td>{escape(label)}</td><td class='tbl-num'>{count}</td></tr>")

    circumference = 2 * 3.14159 * 42
    stroke_dashoffset = circumference * (1 - score_val / 100)
    return f"""
    <div class="report-section" id="synthese">
        <h2 class="section-title">1. {synthese_label}</h2>
        <div class="synthese-gauge-block">
            <span class="synthese-gauge-label">{score_synthese}</span>
            <div class="synthese-gauge-wrapper">
                <svg class="synthese-gauge" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(148,163,184,0.3)" stroke-width="8"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="{score_color}" stroke-width="8" stroke-linecap="round"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
                            transform="rotate(-90 50 50)"/>
                </svg>
                <span class="synthese-gauge-value" style="color:{score_color}">{score_val}</span>
            </div>
        </div>
        <div class="synthese-anomalies-block">
            <span class="synthese-anomalies-value">{len(findings)}</span>
            <span class="synthese-anomalies-label">{anomalies_label}</span>
        </div>
        <h3 class="subsection-title">{tests_label}</h3>
        <table class="data-table">
            <thead><tr><th>{test_label}</th><th>{status_label}</th></tr></thead>
            <tbody>{"".join(test_rows)}</tbody>
        </table>
        <h3 class="subsection-title">{repartition_label}</h3>
        <table class="data-table">
            <thead><tr><th>{cat_label}</th><th>{nb_label}</th></tr></thead>
            <tbody>{"".join(synthese_rows) if synthese_rows else "<tr><td colspan='2'>—</td></tr>"}</tbody>
        </table>
    </div>
    """
