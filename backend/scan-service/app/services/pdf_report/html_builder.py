"""Assemblage du HTML complet du rapport PDF."""

from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.pdf import get_pdf_settings
from app.services.pdf_report.cover import build_cover_page
from app.services.pdf_report.findings import _group_findings_by_category, build_category_sections
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
    sections_html = build_category_sections(by_category, ordered_cats, include_matrices, lang)

    section_num = 2 + sum(1 for c in ordered_cats if by_category.get(c))
    annexes_label = t("annexes", lang)
    annexes_html = f"""
    <div class="report-section" id="annexes">
        <h2 class="section-title">{section_num}. {annexes_label}</h2>
        <p class="annexes-text">{disclaimer}</p>
    </div>
    """

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
        {annexes_html}
        <footer>
            <p>{disclaimer}</p>
            <p>{pdf_settings.footer_url}</p>
        </footer>
    </div>
</body>
</html>
"""
