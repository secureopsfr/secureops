"""Blocs findings et sections par catégorie (rapport PDF)."""

import re
from html import escape
from typing import Any

from app.catalogue.category_summaries import get_category_description, get_checks_count
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


def _markdown_bold_to_html(text: str) -> str:
    """Convertit **texte** en <strong>texte</strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


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
            <span class="finding-title">{section_num}.{finding_idx} {title_f} {badge_html}</span>
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


def _build_category_intro(
    cat: str,
    cat_label: str,
    cat_findings: list[dict[str, Any]],
    section_num: int,
    lang: str,
) -> str:
    """Construit le bloc intro d'une catégorie (2.1 Résumé, description, liste des anomalies).

    Utilisé uniquement pour les catégories avec anomalies.

    Args:
        cat: Identifiant de catégorie.
        cat_label: Libellé affiché (non utilisé, section déjà titrée).
        cat_findings: Findings de la catégorie.
        section_num: Numéro de section (ex. 2 pour « 2.1 Résumé »).
        lang: Code langue (fr/en).

    Returns:
        str: HTML du bloc intro.
    """
    anomaly_count = len(cat_findings)
    anomalies_detected_summary = t("anomalies_detected_summary", lang)
    anomaly_detected_summary = t("anomaly_detected_summary", lang)
    anomalies_one = t("anomalies_one", lang)
    anomalies_word = t("anomalies", lang)
    summary_label = t("summary", lang)

    titles = []
    for f in sorted(cat_findings, key=lambda x: _severity_index(x.get("severity"))):
        slug = f.get("id", "")
        title = get_title(slug, lang) if slug else str(f.get("title", ""))
        titles.append(escape(title))
    titles_str = ", ".join(titles)
    word = anomalies_one if anomaly_count == 1 else anomalies_word
    count_bold = f"<strong>{anomaly_count} {word}</strong>"
    if anomaly_count == 1:
        summary_html = f"{count_bold} {anomaly_detected_summary} : {titles_str}"
    else:
        summary_html = f"{count_bold} {anomalies_detected_summary} : {titles_str}"

    description = get_category_description(cat, lang)
    description_html = ""
    if description:
        desc_escaped = _markdown_bold_to_html(escape(description))
        description_html = f'<p class="category-intro-desc">{desc_escaped}</p>'

    return f"""
    <div class="category-intro" id="sect-{cat}-intro">
        <h3 class="category-intro-title">{section_num}.1 {escape(summary_label)}</h3>
        {description_html}
        <p class="category-intro-summary">{summary_html}</p>
    </div>
    """


def _build_ok_category_subsection(
    section_num: int,
    sub_num: int,
    cat: str,
    cat_label: str,
    lang: str,
) -> str:
    """Construit une sous-section pour une catégorie sans anomalie.

    Args:
        section_num: Numéro de la section parente.
        sub_num: Numéro de sous-section (1, 2, 3...).
        cat: Identifiant de catégorie.
        cat_label: Libellé affiché.
        lang: Code langue (fr/en).

    Returns:
        str: HTML de la sous-section.
    """
    description = get_category_description(cat, lang)
    nb_tests = get_checks_count(cat)
    nb_tests_phrase = t("other_tests_nb_tests_singular", lang) if nb_tests <= 1 else t("other_tests_nb_tests_plural", lang).format(nb=nb_tests)
    if description:
        full_text = f"{description} {nb_tests_phrase}"
    else:
        full_text = nb_tests_phrase
    desc_escaped = _markdown_bold_to_html(escape(full_text))
    description_html = f'<p class="category-intro-desc">{desc_escaped}</p>'
    return f"""
    <div class="other-test-subsection" id="other-{cat}">
        <h3 class="subsection-title">{section_num}.{sub_num} {escape(cat_label)}</h3>
        {description_html}
    </div>
    """


def build_category_sections(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    include_matrices: bool,
    lang: str,
) -> tuple[list[str], int]:
    """Construit les sections HTML pour les catégories avec anomalies.

    Sections 2, 3, ... : uniquement les catégories qui ont des findings.
    Chaque section a : intro (titre, statut, description, résumé) + blocs finding.

    Args:
        by_category: Findings groupés par catégorie.
        ordered_cats: Ordre des catégories.
        include_matrices: Inclure les matrices.
        lang: Code langue (fr/en).

    Returns:
        tuple[list[str], int]: (fragments HTML, numéro de section suivant).
    """
    settings = get_pdf_settings()
    checked_cats = [c for c in settings.categories.checked if c in settings.categories.order] or list(settings.categories.order)
    category_labels = get_category_labels(lang)
    sections_html: list[str] = []
    section_num = 2
    for cat in checked_cats:
        cat_findings = by_category.get(cat, [])
        if not cat_findings:
            continue
        cat_label = category_labels.get(cat, cat)
        sections_html.append(f'<div class="report-section" id="sect-{cat}">')
        sections_html.append(f'<h2 class="section-title">{section_num}. {escape(cat_label)}</h2>')
        intro = _build_category_intro(cat, cat_label, cat_findings, section_num, lang)
        sections_html.append(intro)
        for idx, f in enumerate(sorted(cat_findings, key=lambda x: _severity_index(x.get("severity"))), start=2):
            block = build_finding_block(f, section_num, idx, include_matrices, lang)
            sections_html.append(block)
        sections_html.append("</div>")
        section_num += 1
    return sections_html, section_num


def build_other_tests_section(
    by_category: dict[str, list[dict[str, Any]]],
    section_num: int,
    lang: str,
) -> tuple[str, int]:
    """Construit la section « Autres tests effectués » (catégories sans anomalie).

    Args:
        by_category: Findings groupés par catégorie.
        section_num: Numéro de section à utiliser.
        lang: Code langue (fr/en).

    Returns:
        tuple[str, int]: (HTML de la section ou chaîne vide, numéro suivant).
    """
    settings = get_pdf_settings()
    checked_cats = [c for c in settings.categories.checked if c in settings.categories.order] or list(settings.categories.order)
    category_labels = get_category_labels(lang)
    ok_cats = [c for c in checked_cats if len(by_category.get(c, [])) == 0]
    if not ok_cats:
        return "", section_num

    section_label = t("other_tests_section", lang)
    summary_label = t("summary", lang)
    nb_ok_cats = len(ok_cats)
    nb_total_cats = len(checked_cats)
    nb_ok_tests = sum(get_checks_count(c) for c in ok_cats)
    nb_total_tests = sum(get_checks_count(c) for c in checked_cats)
    ok_cats_label = t("other_tests_cat_singular", lang) if nb_ok_cats <= 1 else t("other_tests_cat_plural", lang)
    ok_tests_label = t("other_tests_test_singular", lang) if nb_ok_tests <= 1 else t("other_tests_test_plural", lang)
    summary_text = t("other_tests_summary", lang).format(
        nb_ok_cats=f"<strong>{nb_ok_cats}</strong>",
        nb_total_cats=f"<strong>{nb_total_cats}</strong>",
        nb_ok_tests=f"<strong>{nb_ok_tests}</strong>",
        nb_total_tests=f"<strong>{nb_total_tests}</strong>",
        ok_cats_label=ok_cats_label,
        ok_tests_label=ok_tests_label,
    )
    subsections_html: list[str] = []
    subsections_html.append(
        f"""
    <div class="category-intro" id="sect-other-tests-intro">
        <h3 class="category-intro-title">{section_num}.1 {escape(summary_label)}</h3>
        <p class="category-intro-summary">{summary_text}</p>
    </div>
    """
    )
    for sub_num, cat in enumerate(ok_cats, start=2):
        cat_label = category_labels.get(cat, cat)
        subsections_html.append(_build_ok_category_subsection(section_num, sub_num, cat, cat_label, lang))

    html = f"""
    <div class="report-section" id="sect-other-tests">
        <h2 class="section-title">{section_num}. {escape(section_label)}</h2>
        {"".join(subsections_html)}
    </div>
    """
    return html, section_num + 1
