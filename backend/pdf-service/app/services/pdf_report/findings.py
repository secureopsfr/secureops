"""Blocs findings et sections par catégorie (rapport PDF)."""

import logging
import re
from html import escape

from app.catalogue.category_summaries import get_category_description, get_checks_count
from app.catalogue.recommendations import get_detail, get_evidence, get_recommendation, get_title
from app.catalogue.risk_matrix import get_gravite, get_vraisemblance
from app.config.pdf import INTRUSIVE_CATEGORY_MAPPING, get_category_config, get_category_labels, get_pdf_settings
from app.schemas.finding import Finding
from app.services.pdf_report.constants import severity_index
from app.services.pdf_report.links import build_inline_ref_links, build_ref_links
from app.services.pdf_report.matrix import render_matrix
from app.services.pdf_report.pdf_i18n import t

logger = logging.getLogger(__name__)


def _severity_badge_style(severity: str) -> tuple[str, str]:
    """Retourne (bg, text) pour le badge de sévérité."""
    settings = get_pdf_settings()
    badges = settings.render.severity_badges
    s = severity.lower()
    style = badges.get(s, badges.get("info", {"bg": "#eff6ff", "text": "#2563eb"}))
    return str(style.get("bg", "#eff6ff")), str(style.get("text", "#2563eb"))


def _severity_label(severity: str, lang: str) -> str:
    """Retourne le libellé de sévérité (fr/en)."""
    key_map = {
        "critical": "severity_critical",
        "high": "severity_high",
        "medium": "severity_medium",
        "low": "severity_low",
        "info": "severity_info",
    }
    key = key_map.get(severity.lower(), "severity_info")
    return t(key, lang)


def _markdown_bold_to_html(text: str) -> str:
    """Convertit **texte** en <strong>texte</strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _truncate(text: str, max_len: int, label: str, slug: str) -> str:
    """Tronque le texte à max_len caractères avec '…' et log si dépassement."""
    if len(text) > max_len:
        logger.warning("text truncated for %s slug=%s (len=%d > %d)", label, slug, len(text), max_len)
        return text[:max_len] + "…"
    return text


def _english_evidence_fallback(title: str, provided_evidence: str) -> str:
    """Avoid leaking French scan evidence in English reports for catalogued findings."""
    context_lines = [line.strip() for line in provided_evidence.splitlines() if line.strip().startswith("Detected on ")]
    fallback = f"Finding detected during the scan: {title}." if title else "Finding detected during the scan."
    return "\n".join([*context_lines, fallback])


def _group_findings_by_category(
    findings: list[Finding],
    lang: str,
    scan_mode: str = "passive",
) -> tuple[dict[str, list[Finding]], list[str]]:
    """Groupe les findings par catégorie (ou macro-catégorie pour intrusif)."""
    cat_config = get_category_config(scan_mode)
    order = list(cat_config.order)
    by_category: dict[str, list[Finding]] = {}
    for f in findings:
        # Pour les scans intrusifs, remapper vers la macro-catégorie
        effective_cat = INTRUSIVE_CATEGORY_MAPPING.get(f.category, "other") if scan_mode == "intrusive" else f.category
        if effective_cat not in by_category:
            by_category[effective_cat] = []
        by_category[effective_cat].append(f)
    ordered_cats = list(order) + [c for c in by_category if c not in order]
    return by_category, ordered_cats


def _split_findings_by_type(findings: list[Finding]) -> tuple[list[Finding], list[Finding]]:
    """Sépare les anomalies des informations."""
    anomaly_findings = [f for f in findings if f.severity.lower() != "info"]
    info_findings = [f for f in findings if f.severity.lower() == "info"]
    return anomaly_findings, info_findings


def build_finding_block(
    f: Finding,
    section_num: int,
    finding_idx: int,
    include_matrices: bool,
    lang: str,
) -> str:
    """Construit le bloc HTML d'un finding.

    Args:
        f: Finding validé.
        section_num: Numéro de section.
        finding_idx: Index du finding dans la section.
        include_matrices: Inclure la matrice gravité/vraisemblance.
        lang: Code langue (fr/en).

    Returns:
        str: HTML du bloc finding.
    """
    render = get_pdf_settings().render

    title_cat = get_title(f.id, lang) if f.id else ""
    title_f = escape(title_cat or f.title)

    severity_display = _severity_label(f.severity, lang)

    catalog_evidence = get_evidence(f.id, lang) if f.id else ""
    provided_evidence = (f.evidence or "").strip()
    if lang == "en" and catalog_evidence:
        raw_evidence = catalog_evidence
    elif lang == "en" and f.id and title_cat:
        raw_evidence = _english_evidence_fallback(title_cat, provided_evidence)
    elif catalog_evidence and provided_evidence and provided_evidence != catalog_evidence:
        raw_evidence = f"{provided_evidence}\n{catalog_evidence}"
    else:
        raw_evidence = provided_evidence or catalog_evidence
    evidence_text = _truncate(raw_evidence, render.evidence_max_len, "evidence", f.id)
    evidence = escape(evidence_text).replace("\n", "<br/>")

    raw_rec = get_recommendation(f.id, lang) if f.id else f.recommendation
    rec_text = _truncate(raw_rec, render.recommendation_max_len, "recommendation", f.id)
    recommendation = escape(rec_text)

    gravite = get_gravite(f.id) if f.id else ""
    vraisemblance = get_vraisemblance(f.id) if f.id else ""
    badge_bg, badge_text = _severity_badge_style(f.severity)
    detail_text = get_detail(f.id, lang) if f.id else ""

    evidence_label = t("evidence", lang)
    detail_label = t("detail", lang)
    how_to_fix_label = t("how_to_fix", lang)
    learn_more = t("learn_more", lang)

    refs_html = build_ref_links(f.references, max_count=render.references_max_list)

    detail_html = ""
    if detail_text:
        refs_line = build_inline_ref_links(f.references, max_count=render.references_max_inline, prefix=learn_more)
        detail_html = f"""
        <div class="finding-detail">
            <p><strong>{detail_label}:</strong> {escape(detail_text)}</p>
            {refs_line}
        </div>
        """

    owasp_cats = getattr(f, "owasp_categories", None) or []
    owasp_html = ""
    if owasp_cats:
        owasp_str = ", ".join(owasp_cats)
        owasp_label = t("owasp", lang)
        owasp_html = f' <span class="finding-owasp" title="{owasp_label}">{escape(owasp_str)}</span>'
    badge_html = f'<span class="finding-badge" style="background:{badge_bg};color:{badge_text}">{escape(severity_display)}</span>{owasp_html}'
    block = f"""
    <div class="finding-block" id="finding-{section_num}-{finding_idx}">
        <h3 class="finding-title-row">
            <span class="finding-title">{section_num}.{finding_idx} {title_f} {badge_html}</span>
        </h3>
        <p class="finding-evidence"><strong>{evidence_label}:</strong> {evidence}</p>
        {detail_html}
    """
    if include_matrices and f.id and gravite and vraisemblance:
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
    anomaly_findings: list[Finding],
    info_findings: list[Finding],
    section_num: int,
    lang: str,
) -> str:
    """Construit le bloc intro d'une catégorie (x.1 Résumé, anomalies et infos).

    Args:
        cat: Identifiant de catégorie.
        cat_label: Libellé affiché (non utilisé, section déjà titrée).
        anomaly_findings: Anomalies de la catégorie.
        info_findings: Informations de la catégorie.
        section_num: Numéro de section (ex. 2 pour « 2.1 Résumé »).
        lang: Code langue (fr/en).

    Returns:
        str: HTML du bloc intro.
    """
    anomaly_count = len(anomaly_findings)
    info_count = len(info_findings)
    anomalies_detected_summary = t("anomalies_detected_summary", lang)
    anomaly_detected_summary = t("anomaly_detected_summary", lang)
    anomalies_one = t("anomalies_one", lang)
    anomalies_word = t("anomalies", lang)
    infos_one = t("infos_one", lang)
    infos_word = t("infos", lang)
    infos_detected_summary = t("infos_detected_summary", lang)
    info_detected_summary = t("info_detected_summary", lang)
    no_anomaly_detected = t("no_anomaly_detected", lang)
    summary_label = t("summary", lang)

    anomaly_titles = []
    for f in sorted(anomaly_findings, key=lambda x: severity_index(x.severity)):
        title = get_title(f.id, lang) if f.id else f.title
        anomaly_titles.append(escape(title))

    info_titles = []
    for f in sorted(info_findings, key=lambda x: severity_index(x.severity)):
        title = get_title(f.id, lang) if f.id else f.title
        info_titles.append(escape(title))

    summary_lines: list[str] = []
    if anomaly_count:
        anomaly_titles_str = ", ".join(anomaly_titles)
        word = anomalies_one if anomaly_count == 1 else anomalies_word
        count_bold = f"<strong>{anomaly_count} {word}</strong>"
        summary_text = anomaly_detected_summary if anomaly_count == 1 else anomalies_detected_summary
        summary_lines.append(f"{count_bold} {summary_text} : {anomaly_titles_str}")
    else:
        summary_lines.append(escape(no_anomaly_detected))

    if info_count:
        info_titles_str = ", ".join(info_titles)
        word = infos_one if info_count == 1 else infos_word
        count_bold = f"<strong>{info_count} {word}</strong>"
        summary_text = info_detected_summary if info_count == 1 else infos_detected_summary
        summary_lines.append(f"{count_bold} {summary_text} : {info_titles_str}")

    summary_html = "<br/>".join(summary_lines)

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
    by_category: dict[str, list[Finding]],
    ordered_cats: list[str],
    include_matrices: bool,
    lang: str,
    scan_mode: str = "passive",
    info_by_category: dict[str, list[Finding]] | None = None,
) -> tuple[list[str], int]:
    """Construit les sections HTML pour les catégories avec anomalies ou infos."""
    cat_config = get_category_config(scan_mode)
    checked_cats = [c for c in cat_config.checked if c in cat_config.order] or list(cat_config.order)
    category_labels = get_category_labels(lang, scan_mode=scan_mode)
    info_by_category = info_by_category or {}
    sections_html: list[str] = []
    section_num = 2
    for cat in checked_cats:
        anomaly_findings = by_category.get(cat, [])
        info_findings = info_by_category.get(cat, [])
        if not anomaly_findings and not info_findings:
            continue
        cat_label = category_labels.get(cat, cat)
        sections_html.append(f'<div class="report-section" id="sect-{cat}">')
        sections_html.append(f'<h2 class="section-title">{section_num}. {escape(cat_label)}</h2>')
        intro = _build_category_intro(cat, cat_label, anomaly_findings, info_findings, section_num, lang)
        sections_html.append(intro)
        all_findings = [*anomaly_findings, *info_findings]
        for idx, f in enumerate(sorted(all_findings, key=lambda x: severity_index(x.severity)), start=2):
            block = build_finding_block(f, section_num, idx, include_matrices, lang)
            sections_html.append(block)
        sections_html.append("</div>")
        section_num += 1
    return sections_html, section_num


def _build_info_intro(
    info_findings: list[Finding],
    section_num: int,
    lang: str,
) -> str:
    """Construit le résumé de la section informations."""
    info_count = len(info_findings)
    summary_label = t("summary", lang)
    infos_one = t("infos_one", lang)
    infos_word = t("infos", lang)
    infos_detected_summary = t("infos_detected_summary", lang)
    info_detected_summary = t("info_detected_summary", lang)
    word = infos_one if info_count == 1 else infos_word

    titles = []
    for f in sorted(info_findings, key=lambda x: severity_index(x.severity)):
        title = get_title(f.id, lang) if f.id else f.title
        titles.append(escape(title))
    titles_str = ", ".join(titles)
    summary_text = info_detected_summary if info_count == 1 else infos_detected_summary

    return f"""
    <div class="category-intro" id="sect-infos-intro">
        <h3 class="category-intro-title">{section_num}.1 {escape(summary_label)}</h3>
        <p class="category-intro-summary"><strong>{info_count} {word}</strong> {summary_text} : {titles_str}</p>
    </div>
    """


def build_info_section(
    info_findings: list[Finding],
    section_num: int,
    include_matrices: bool,
    lang: str,
) -> tuple[str, int]:
    """Construit la section dédiée aux findings informatifs."""
    if not info_findings:
        return "", section_num

    section_label = t("infos_section", lang)
    sections_html = [
        f"""
    <div class="report-section report-section-infos" id="sect-infos">
        <h2 class="section-title">{section_num}. {escape(section_label)}</h2>
        {_build_info_intro(info_findings, section_num, lang)}
    """
    ]
    for idx, f in enumerate(sorted(info_findings, key=lambda x: severity_index(x.severity)), start=2):
        sections_html.append(build_finding_block(f, section_num, idx, include_matrices, lang))
    sections_html.append("</div>")
    return "".join(sections_html), section_num + 1


def build_other_tests_section(
    by_category: dict[str, list[Finding]],
    section_num: int,
    lang: str,
    scan_mode: str = "passive",
) -> tuple[str, int]:
    """Construit la section « Autres tests effectués » (catégories sans anomalie)."""
    cat_config = get_category_config(scan_mode)
    checked_cats = [c for c in cat_config.checked if c in cat_config.order] or list(cat_config.order)
    category_labels = get_category_labels(lang, scan_mode=scan_mode)
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
