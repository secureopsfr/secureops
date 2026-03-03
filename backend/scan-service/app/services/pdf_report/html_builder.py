"""Assemblage du HTML complet du rapport PDF."""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from app.config.pdf import get_pdf_settings
from app.services.pdf_report.cover import build_cover_page
from app.services.pdf_report.findings import (
    _group_findings_by_category,
    build_category_sections,
    build_other_tests_section,
)
from app.services.pdf_report.pdf_i18n import t
from app.services.pdf_report.sommaire import build_sommaire
from app.services.pdf_report.synthese import build_synthese

_STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
_CSS_PATH = _STATIC_DIR / "pdf_report.css"


def _load_css() -> str:
    """Charge le CSS du rapport PDF."""
    if _CSS_PATH.is_file():
        return _CSS_PATH.read_text(encoding="utf-8")
    return ""


def _normalize_lang(lang: str) -> str:
    """Force lang à fr ou en."""
    return "en" if lang == "en" else "fr"


def _build_references_section(
    findings: list[dict[str, Any]],
    section_num: int,
    lang: str,
) -> str:
    """Construit la section Références (tous les liens du rapport).

    Args:
        findings: Liste des findings (chacun peut avoir references).
        section_num: Numéro de section.
        lang: Code langue (fr/en).

    Returns:
        str: HTML de la section Références.
    """
    all_refs: set[str] = set()
    for f in findings:
        refs = f.get("references") or []
        for ref in refs:
            url = str(ref).strip()
            if url and url.startswith(("http://", "https://")):
                all_refs.add(url)
    sorted_refs = sorted(all_refs)
    section_label = t("references_section", lang)
    if not sorted_refs:
        empty_msg = t("references_empty", lang)
        return f"""
    <div class="report-section" id="references">
        <h2 class="section-title">{section_num}. {escape(section_label)}</h2>
        <p class="references-empty">{escape(empty_msg)}</p>
    </div>
    """
    items = [
        (
            f'<li class="references-item"><a href="{escape(url)}" class="references-link" '
            f'target="_blank" rel="noopener noreferrer">{escape(url)}</a></li>'
        )
        for url in sorted_refs
    ]
    return f"""
    <div class="report-section" id="references">
        <h2 class="section-title">{section_num}. {escape(section_label)}</h2>
        <ul class="references-list">{"".join(items)}</ul>
    </div>
    """


def build_html(
    url: str,
    score: int | None,
    timestamp: str,
    duration: float,
    findings: list[dict[str, Any]],
    include_matrices: bool = True,
    lang: str = "fr",
) -> str:
    """Construit le HTML complet du rapport.

    Args:
        url: URL scannée.
        score: Score /100.
        timestamp: Horodatage ISO.
        duration: Durée en secondes.
        findings: Liste des findings (id, category, title, severity, evidence, recommendation, references).
        include_matrices: Inclure les matrices par finding.
        lang: Code langue (fr/en).

    Returns:
        str: Document HTML complet.
    """
    lang = _normalize_lang(lang)
    pdf_settings = get_pdf_settings()

    title = t("page_title", lang)
    disclaimer = t("disclaimer", lang)
    report_title = t("report_title", lang)
    subtitle = t("subtitle", lang)

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y %H:%M") if lang == "fr" else dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        date_str = timestamp

    score_val = score or 0
    score_color = "#10b981" if score_val >= 80 else "#f59e0b" if score_val >= 50 else "#ef4444"

    by_category, ordered_cats = _group_findings_by_category(findings, lang)
    cover_page = build_cover_page(url, date_str, lang, report_title, subtitle)
    sommaire_html = build_sommaire(by_category, ordered_cats, lang)
    synthese_html = build_synthese(by_category, ordered_cats, findings, score_val, score_color, lang)
    sections_html, next_section_num = build_category_sections(by_category, ordered_cats, include_matrices, lang)
    other_tests_html, next_section_num = build_other_tests_section(by_category, next_section_num, lang)

    references_html = _build_references_section(findings, next_section_num, lang)

    css_content = _load_css()
    style_tag = f"<style>\n{css_content}\n</style>" if css_content else ""

    return f"""
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{title} - SecureOps</title>
    {style_tag}
</head>
<body>
    {cover_page}
    <div class="report-body">
        {sommaire_html}
        {synthese_html}
        {"".join(sections_html)}
        {other_tests_html}
        {references_html}
        <footer>
            <p>{disclaimer}</p>
            <p>{pdf_settings.footer_url}</p>
        </footer>
    </div>
</body>
</html>
"""
