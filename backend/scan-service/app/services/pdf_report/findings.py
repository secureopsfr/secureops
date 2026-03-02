"""Blocs findings et sections par catégorie (rapport PDF)."""

from html import escape
from typing import Any

from app.catalogue.recommendations import get_detail, get_evidence, get_recommendation, get_title
from app.catalogue.risk_matrix import get_gravite, get_vraisemblance
from app.config.pdf import get_category_labels, get_pdf_settings
from app.services.pdf_report.links import build_inline_ref_links, build_ref_links
from app.services.pdf_report.matrix import render_matrix
from app.services.pdf_report.pdf_i18n import t

_SEVERITY_BADGE = {
    "critical": {"bg": "#fef2f2", "text": "#dc2626"},
    "high": {"bg": "#fffbeb", "text": "#d97706"},
    "medium": {"bg": "#fffbeb", "text": "#d97706"},
    "low": {"bg": "#eff6ff", "text": "#2563eb"},
    "info": {"bg": "#eff6ff", "text": "#2563eb"},
}


def _severity_index(severity: str) -> int:
    """Retourne l'index de tri pour la sévérité (critical=0, info=4)."""
    order = ["critical", "high", "medium", "low", "info"]
    s = severity or "info"
    return order.index(s) if s in order else 99


def _severity_badge_style(severity: str) -> tuple[str, str]:
    """Retourne (bg, text) pour le badge de sévérité."""
    s = (severity or "info").lower()
    style = _SEVERITY_BADGE.get(s, _SEVERITY_BADGE["info"])
    return style["bg"], style["text"]


def _severity_label(severity: str, lang: str) -> str:
    """Retourne le libellé de sévérité (fr/en)."""
    key_map = {
        "critical": "severity_critical",
        "high": "severity_high",
        "medium": "severity_medium",
        "low": "severity_low",
        "info": "severity_info",
    }
    s = (severity or "info").lower()
    key = key_map.get(s, "severity_info")
    return t(key, lang)


def _group_findings_by_category(
    findings: list[dict[str, Any]],
    lang: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Groupe les findings par catégorie et retourne l'ordre des catégories."""
    settings = get_pdf_settings()
    order = list(settings.categories.order)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        cat = f.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f)
    ordered_cats = list(order) + [c for c in by_category if c not in order]
    return by_category, ordered_cats


def build_finding_block(
    f: dict[str, Any],
    section_num: int,
    finding_idx: int,
    include_matrices: bool,
    lang: str,
) -> str:
    """Construit le bloc HTML d'un finding.

    Args:
        f: Finding (id, title, severity, evidence, recommendation, references).
        section_num: Numéro de section.
        finding_idx: Index du finding dans la section.
        include_matrices: Inclure la matrice gravité/vraisemblance.
        lang: Code langue (fr/en).

    Returns:
        str: HTML du bloc finding.
    """
    slug = f.get("id", "")
    title_cat = get_title(slug, lang) if slug else ""
    title_f = escape(title_cat or str(f.get("title", "")))
    severity = (f.get("severity") or "info").lower()
    severity_display = _severity_label(severity, lang)
    evidence_cat = get_evidence(slug, lang) if slug else ""
    evidence = escape(str(evidence_cat or f.get("evidence", ""))[:800])
    rec_text = get_recommendation(slug, lang) if slug else str(f.get("recommendation", ""))
    recommendation = escape(rec_text[:800])
    references = f.get("references") or []
    gravite = get_gravite(slug) if slug else ""
    vraisemblance = get_vraisemblance(slug) if slug else ""
    badge_bg, badge_text = _severity_badge_style(severity)
    detail_text = get_detail(slug, lang) if slug else ""

    evidence_label = t("evidence", lang)
    detail_label = t("detail", lang)
    how_to_fix_label = t("how_to_fix", lang)
    learn_more = t("learn_more", lang)

    refs_html = build_ref_links(references, lang, max_count=10)

    detail_html = ""
    if detail_text:
        refs_line = build_inline_ref_links(references, lang, max_count=3, prefix=learn_more)
        detail_html = f"""
        <div class="finding-detail">
            <p><strong>{detail_label}:</strong> {escape(detail_text)}</p>
            {refs_line}
        </div>
        """

    badge_html = f'<span class="finding-badge" style="background:{badge_bg};color:{badge_text}">{escape(severity_display)}</span>'
    block = f"""
    <div class="finding-block" id="finding-{section_num}-{finding_idx}">
        <h3 class="finding-title-row">
            <span class="finding-title">{section_num}.{finding_idx} – {title_f} {badge_html}</span>
        </h3>
        <p class="finding-evidence"><strong>{evidence_label}:</strong> {evidence}</p>
        {detail_html}
    """
    if include_matrices and slug and gravite and vraisemblance:
        block += f"""
        <div class="finding-matrix">{render_matrix(gravite, vraisemblance, lang)}</div>
        """
    block += f"""
        <div class="finding-howtofix">
            <p class="finding-howtofix-label">{how_to_fix_label}</p>
            <p class="finding-recommendation">{recommendation}</p>
            {refs_html}
        </div>
    </div>
    """
    return block


def build_category_sections(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    include_matrices: bool,
    lang: str,
) -> list[str]:
    """Construit les sections HTML par catégorie.

    Args:
        by_category: Findings groupés par catégorie.
        ordered_cats: Ordre des catégories.
        include_matrices: Inclure les matrices.
        lang: Code langue (fr/en).

    Returns:
        list[str]: Liste de fragments HTML.
    """
    category_labels = get_category_labels(lang)
    sections_html: list[str] = []
    section_num = 2
    for cat in ordered_cats:
        cat_findings = by_category.get(cat, [])
        if not cat_findings:
            continue
        cat_label = category_labels.get(cat, cat)
        sections_html.append(f'<div class="report-section" id="sect-{cat}">')
        sections_html.append(f'<h2 class="section-title">{section_num}. {escape(cat_label)}</h2>')
        for idx, f in enumerate(sorted(cat_findings, key=lambda x: _severity_index(x.get("severity"))), start=1):
            block = build_finding_block(f, section_num, idx, include_matrices, lang)
            sections_html.append(block)
        sections_html.append("</div>")
        section_num += 1
    return sections_html
