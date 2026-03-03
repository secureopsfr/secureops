"""Section Synthèse du rapport PDF."""

from html import escape
from typing import Any

from app.catalogue.category_summaries import get_checks_count
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
    status_label = t("status", lang)
    status_ok = t("status_ok", lang)
    anomalies_word = t("anomalies", lang)
    anomalies_one = t("anomalies_one", lang)
    repartition_label = t("repartition", lang)
    cat_label = t("category", lang)
    nb_tests_label = t("nb_tests", lang)
    anomalies_label = t("anomalies_detected", lang)
    anomaly_label = t("anomaly_detected", lang)

    settings = get_pdf_settings()
    checked_cats = settings.categories.checked
    category_labels = get_category_labels(lang)

    synthese_rows = []
    for cat in checked_cats:
        anomaly_count = len(by_category.get(cat, []))
        checks_count = get_checks_count(cat)
        label = category_labels.get(cat, cat)
        if anomaly_count == 0:
            status_html = f'<span class="status-ok">{status_ok}</span>'
        else:
            word = anomalies_one if anomaly_count == 1 else anomalies_word
            status_html = f'<a href="#sect-{escape(cat)}" class="status-warning status-link">' f"{anomaly_count} {word}</a>"
        synthese_rows.append(f"<tr><td>{escape(label)}</td><td class='tbl-num'>{checks_count}</td>" f"<td>{status_html}</td></tr>")

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
            <span class="synthese-anomalies-label">{anomaly_label if len(findings) == 1 else anomalies_label}</span>
        </div>
        <h3 class="subsection-title">{repartition_label}</h3>
        <table class="data-table">
            <thead><tr><th>{cat_label}</th><th>{nb_tests_label}</th><th>{status_label}</th></tr></thead>
            <tbody>{"".join(synthese_rows) if synthese_rows else "<tr><td colspan='3'>—</td></tr>"}</tbody>
        </table>
    </div>
    """
