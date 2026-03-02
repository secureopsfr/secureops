"""Sommaire du rapport PDF (sections et sous-parties)."""

from html import escape
from typing import Any

from app.config.pdf import get_category_labels
from app.services.pdf_report.pdf_i18n import t


def _severity_index(severity: str) -> int:
    """Retourne l'index de tri pour la sévérité (critical=0, info=4)."""
    order = ["critical", "high", "medium", "low", "info"]
    s = severity or "info"
    return order.index(s) if s in order else 99


def build_sommaire(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    lang: str,
) -> str:
    """Construit le HTML du sommaire (sections et sous-parties 2.1, 2.2, etc.).

    Args:
        by_category: Findings groupés par catégorie.
        ordered_cats: Ordre des catégories.
        lang: Code langue (fr/en).

    Returns:
        str: HTML du sommaire.
    """
    sommaire_label = t("sommaire", lang)
    synthese_label = t("synthese", lang)
    annexes_label = t("annexes", lang)
    category_labels = get_category_labels(lang)

    items = [f'<li class="toc-item"><a href="#synthese" class="toc-link"><span class="toc-num">1</span> {synthese_label}</a></li>']
    section_num = 2
    for cat in ordered_cats:
        cat_findings = by_category.get(cat, [])
        if not cat_findings:
            continue
        label = category_labels.get(cat, cat)
        items.append(
            f'<li class="toc-item"><a href="#sect-{cat}" class="toc-link"><span class="toc-num">{section_num}</span> {escape(label)}</a></li>'
        )
        for idx, f in enumerate(sorted(cat_findings, key=lambda x: _severity_index(x.get("severity"))), start=1):
            title = escape(str(f.get("title", "")))
            items.append(
                f'<li class="toc-item toc-sub"><a href="#finding-{section_num}-{idx}" class="toc-link">'
                f'<span class="toc-num">{section_num}.{idx}</span> {title}</a></li>'
            )
        section_num += 1
    items.append(f'<li class="toc-item"><a href="#annexes" class="toc-link"><span class="toc-num">{section_num}</span> {annexes_label}</a></li>')
    return f"""
    <div class="report-section sommaire" id="sommaire">
        <h2 class="section-title">{sommaire_label}</h2>
        <ol class="toc-list">{"".join(items)}</ol>
    </div>
    """
