"""Service de génération de rapports PDF pour les scans de posture sécurité.

Génère un PDF avec en-tête, score, findings et une matrice gravité/vraisemblance
par finding (croix dans la cellule correspondante).
"""

import base64
import io
import os
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from weasyprint import HTML

from app.catalogue.risk_matrix import get_gravite, get_vraisemblance

# Logo : PDF_LOGO_PATH ou app/static/logo.png par défaut
_DEFAULT_LOGO_PATH = Path(__file__).resolve().parent.parent / "static" / "logo.png"

# SVG fallback si pas de logo (bouclier sécurité)
_LOGO_SVG_FALLBACK = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="64" height="64">'
    '<path fill="#38bdf8" d="M24 4L6 10v10c0 11 8 20 18 24 10-4 18-13 18-24V10L24 4z"/>'
    '<path fill="#0f172a" d="M24 8L10 12.5v7.5c0 8.5 6 15.5 14 18.5 8-3 14-10 14-18.5V12.5L24 8z"/>'
    '<circle cx="24" cy="22" r="6" fill="#38bdf8"/>'
    "</svg>"
)


def _get_logo_data_uri() -> str | None:
    """Retourne le logo en data URI (base64) ou None pour utiliser le SVG fallback."""
    path_str = os.getenv("PDF_LOGO_PATH")
    path = Path(path_str) if path_str else _DEFAULT_LOGO_PATH
    if not path.is_file():
        return None
    try:
        data = path.read_bytes()
        ext = path.suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/svg+xml"
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except (OSError, ValueError):
        return None


# Ordre et libellés des catégories (fr/en)
_CATEGORY_ORDER = (
    "tls",
    "headers",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "tech_fingerprinting",
    "other",
)
# Catégories de vérifications toujours exécutées par le scan (hors "other")
_CHECKED_CATEGORIES = (
    "tls",
    "headers",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "tech_fingerprinting",
)
_CATEGORY_LABELS_FR = {
    "tls": "TLS / HTTPS",
    "headers": "Security Headers",
    "cookies": "Cookies",
    "exposed_files": "Fichiers exposés",
    "directory_listing": "Directory listing",
    "robots_txt": "robots.txt",
    "tech_fingerprinting": "Tech fingerprinting",
    "other": "Autres",
}
_CATEGORY_LABELS_EN = {
    "tls": "TLS / HTTPS",
    "headers": "Security Headers",
    "cookies": "Cookies",
    "exposed_files": "Exposed files",
    "directory_listing": "Directory listing",
    "robots_txt": "robots.txt",
    "tech_fingerprinting": "Tech fingerprinting",
    "other": "Other",
}

# Couleurs de la matrice (docs/verifications)
_COLORS = [
    ["#22c55e", "#22c55e", "#facc15", "#facc15"],  # Mineure
    ["#22c55e", "#facc15", "#f97316", "#f97316"],  # Significative
    ["#facc15", "#f97316", "#ef4444", "#ef4444"],  # Importante
    ["#f97316", "#ef4444", "#ef4444", "#ef4444"],  # Majeure
]
_GRAVITES = ("Mineure", "Significative", "Importante", "Majeure")
_VRAISEMBLANCES = ("Très faible", "Faible", "Forte", "Très forte")

# Couleurs des badges de sévérité (alignées avec le scanner frontend)
_SEVERITY_BADGE = {
    "critical": {"bg": "#fef2f2", "text": "#dc2626"},
    "high": {"bg": "#fffbeb", "text": "#d97706"},
    "medium": {"bg": "#fffbeb", "text": "#d97706"},
    "low": {"bg": "#eff6ff", "text": "#2563eb"},
    "info": {"bg": "#eff6ff", "text": "#2563eb"},
}


def _gravite_index(gravite: str) -> int:
    """Retourne l'index de ligne pour la gravité."""
    try:
        return _GRAVITES.index(gravite)
    except ValueError:
        return 1


def _vraisemblance_index(vraisemblance: str) -> int:
    """Retourne l'index de colonne pour la vraisemblance."""
    try:
        return _VRAISEMBLANCES.index(vraisemblance)
    except ValueError:
        return 2


def _render_matrix(gravite: str, vraisemblance: str) -> str:
    """Génère le HTML d'une matrice avec croix à la position (gravité, vraisemblance).

    Args:
        gravite: Ligne (Mineure, Significative, Importante, Majeure).
        vraisemblance: Colonne (Très faible, Faible, Forte, Très forte).

    Returns:
        str: Fragment HTML de la matrice.
    """
    row_idx = _gravite_index(gravite)
    col_idx = _vraisemblance_index(vraisemblance)

    th_style = "border:1px solid #333;padding:4px 6px;font-weight:600;font-size:9px"
    rows = []
    header_cells = f"<th style='{th_style}'>Gravité \\ Vraisemblance</th>" + "".join(
        f"<th style='{th_style}'>{escape(v)}</th>" for v in _VRAISEMBLANCES
    )
    rows.append(f"<tr>{header_cells}</tr>")

    for i, grav in enumerate(_GRAVITES):
        cells = []
        for j in range(4):
            bg = _COLORS[i][j]
            cross = "✗" if (i == row_idx and j == col_idx) else ""
            style = f"border:1px solid #333;padding:6px;background-color:{bg};min-width:45px;text-align:center;font-size:10px"
            cells.append(f"<td style='{style}'>{escape(cross)}</td>")
        row_label = f"<td style='{th_style}'>{escape(grav)}</td>"
        rows.append(f"<tr>{row_label}{''.join(cells)}</tr>")

    return f"<table style='border-collapse:collapse;margin:12px 0'>{''.join(rows)}</table>"


def _get_risk_level(gravite: str, vraisemblance: str, lang: str) -> str:
    """Dérive le niveau de risque (Élevé/Moyen/Faible) à partir de gravité et vraisemblance."""
    gi = _gravite_index(gravite)
    vi = _vraisemblance_index(vraisemblance)
    # Score simplifié : plus la position est en bas-droite, plus le risque est élevé
    score = gi * 4 + vi
    if score >= 10:
        return "Risque élevé" if lang == "fr" else "High risk"
    if score >= 6:
        return "Risque moyen" if lang == "fr" else "Medium risk"
    return "Risque faible" if lang == "fr" else "Low risk"


def _severity_index(severity: str) -> int:
    """Retourne l'index de tri pour la sévérité (critical=0, info=4)."""
    order = ["critical", "high", "medium", "low", "info"]
    s = severity or "info"
    return order.index(s) if s in order else 99


def _group_findings_by_category(findings: list[dict[str, Any]], lang: str) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Groupe les findings par catégorie et retourne l'ordre des catégories."""
    category_labels = _CATEGORY_LABELS_FR if lang == "fr" else _CATEGORY_LABELS_EN
    by_category: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        cat = f.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f)
    ordered_cats = list(_CATEGORY_ORDER) + [c for c in by_category if c not in _CATEGORY_ORDER]
    return by_category, ordered_cats


def _build_cover_page(url: str, date_str: str, lang: str, report_title: str, subtitle: str) -> str:
    """Construit le HTML de la page de garde."""
    url_label = "URL scannée" if lang == "fr" else "Scanned URL"
    date_label = "Date" if lang == "fr" else "Date"
    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")[:60]
    if len(url) > 60:
        display_url += "…"
    logo_data = _get_logo_data_uri()
    logo_html = (
        f'<img src="{logo_data}" alt="SecureOps" class="cover-logo-img" />'
        if logo_data
        else f'<span class="cover-logo-svg">{_LOGO_SVG_FALLBACK}</span>'
    )
    return f"""
    <div class="cover-page" style="page-break-after:always">
        <div class="cover-content">
            <div class="cover-logo-top">{logo_html}</div>
            <div class="cover-brand">
                <span class="cover-logo">SecureOps</span>
                <span class="cover-tagline">{subtitle}</span>
            </div>
            <h1 class="cover-title">{report_title}</h1>
            <div class="cover-meta">
                <div class="cover-meta-row cover-meta-inline">
                    <span><span class="cover-meta-label">{url_label}</span> <span class="cover-meta-value">{escape(display_url)}</span></span>
                    <span class="cover-meta-sep">•</span>
                    <span><span class="cover-meta-label">{date_label}</span> <span class="cover-meta-value">{date_str}</span></span>
                </div>
            </div>
        </div>
    </div>
    """


def _build_sommaire(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    category_labels: dict[str, str],
    lang: str,
) -> str:
    """Construit le HTML du sommaire."""
    sommaire_label = "Sommaire" if lang == "fr" else "Table of contents"
    synthese_label = "Synthèse du scan" if lang == "fr" else "Scan summary"
    annexes_label = "Annexes" if lang == "fr" else "Appendix"
    items = [f'<li class="toc-item"><a href="#synthese" class="toc-link"><span class="toc-num">1</span> {synthese_label}</a></li>']
    section_num = 2
    for cat in ordered_cats:
        if by_category.get(cat):
            label = category_labels.get(cat, cat)
            items.append(
                f'<li class="toc-item"><a href="#sect-{cat}" class="toc-link"><span class="toc-num">{section_num}</span> {escape(label)}</a></li>'
            )
            section_num += 1
    items.append(f'<li class="toc-item"><a href="#annexes" class="toc-link"><span class="toc-num">{section_num}</span> {annexes_label}</a></li>')
    return f"""
    <div class="report-section sommaire" id="sommaire">
        <h2 class="section-title">{sommaire_label}</h2>
        <ol class="toc-list">{"".join(items)}</ol>
    </div>
    """


def _build_synthese(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    category_labels: dict[str, str],
    findings: list[dict[str, Any]],
    score_val: int,
    score_color: str,
    lang: str,
) -> str:
    """Construit le HTML de la section Synthèse."""
    synthese_label = "Synthèse du scan" if lang == "fr" else "Scan summary"
    score_synthese = "Score" if lang == "fr" else "Score"
    tests_label = "Tests effectués" if lang == "fr" else "Tests performed"
    test_label = "Test" if lang == "fr" else "Test"
    status_label = "Statut" if lang == "fr" else "Status"
    status_ok = "OK" if lang == "fr" else "OK"
    status_anomalies_fr = "anomalies"
    status_anomalies_en = "findings"
    repartition_label = "Répartition par catégorie" if lang == "fr" else "Breakdown by category"
    cat_label = "Catégorie" if lang == "fr" else "Category"
    nb_label = "Nb" if lang == "fr" else "Count"
    anomalies_label = "anomalies détectées" if lang == "fr" else "findings detected"
    anomalies_word = status_anomalies_fr if lang == "fr" else status_anomalies_en

    # Tableau des tests effectués avec statut (OK / X anomalies)
    test_rows = []
    for cat in _CHECKED_CATEGORIES:
        count = len(by_category.get(cat, []))
        label = category_labels.get(cat, cat)
        if count == 0:
            status_html = f'<span class="status-ok">{status_ok}</span>'
        else:
            status_html = f'<span class="status-fail">{count} {anomalies_word}</span>'
        test_rows.append(f"<tr><td>{escape(label)}</td><td>{status_html}</td></tr>")

    # Répartition par catégorie (catégories avec findings uniquement)
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


def _severity_badge_style(severity: str) -> tuple[str, str]:
    """Retourne (bg, text) pour le badge de sévérité."""
    s = (severity or "info").lower()
    style = _SEVERITY_BADGE.get(s, _SEVERITY_BADGE["info"])
    return style["bg"], style["text"]


def _severity_label(severity: str, lang: str) -> str:
    """Retourne le libellé de sévérité (fr/en)."""
    labels_fr = {"critical": "Critique", "high": "Élevé", "medium": "Moyen", "low": "Faible", "info": "Info"}
    labels_en = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low", "info": "Info"}
    labels = labels_fr if lang == "fr" else labels_en
    return labels.get((severity or "info").lower(), severity or "Info")


def _build_finding_block(
    f: dict[str, Any],
    section_num: int,
    finding_idx: int,
    severity_label: str,
    contexte_label: str,
    impact_label: str,
    matrice_label: str,
    risque_label: str,
    conseils_label: str,
    include_matrices: bool,
    lang: str,
) -> str:
    """Construit le bloc HTML d'un finding (2.1, 2.2…, badge, contexte, impact, matrice, conseils)."""
    slug = f.get("id", "")
    title_f = escape(str(f.get("title", "")))
    severity = (f.get("severity") or "info").lower()
    severity_display = _severity_label(severity, lang)
    evidence = escape(str(f.get("evidence", ""))[:800])
    recommendation = escape(str(f.get("recommendation", ""))[:800])
    gravite = get_gravite(slug) if slug else ""
    vraisemblance = get_vraisemblance(slug) if slug else ""
    badge_bg, badge_text = _severity_badge_style(severity)

    impact_text = f"Gravité : {gravite}." if gravite else f"{severity_label} : {severity_display}."
    block = f"""
    <div class="finding-block">
        <div class="finding-header">
            <h3 class="finding-title">{section_num}.{finding_idx} – {title_f}</h3>
            <span class="finding-badge" style="background:{badge_bg};color:{badge_text}">{escape(severity_display)}</span>
        </div>
        <p class="finding-contexte"><strong>{contexte_label}</strong> {evidence}</p>
        <p class="finding-impact"><strong>{impact_label}</strong> {impact_text}</p>
    """
    if include_matrices and slug and gravite and vraisemblance:
        risk_level = _get_risk_level(gravite, vraisemblance, lang)
        block += f"""
        <p class="finding-matrice-label"><strong>{matrice_label}</strong></p>
        <div class="finding-matrix">{_render_matrix(gravite, vraisemblance)}</div>
        <p class="finding-risque-label"><strong>{risque_label}</strong> {risk_level}</p>
        """
    block += f"""
        <p class="finding-conseils"><strong>{conseils_label}</strong> {recommendation}</p>
    </div>
    """
    return block


def _build_category_sections(
    by_category: dict[str, list[dict[str, Any]]],
    ordered_cats: list[str],
    category_labels: dict[str, str],
    severity_label: str,
    include_matrices: bool,
    lang: str,
) -> list[str]:
    """Construit les sections HTML par catégorie."""
    contexte_label = "Contexte" if lang == "fr" else "Context"
    impact_label = "Impact" if lang == "fr" else "Impact"
    matrice_label = "Gravité / Vraisemblance" if lang == "fr" else "Severity / Likelihood"
    risque_label = "Risque identifié" if lang == "fr" else "Identified risk"
    conseils_label = "Conseils" if lang == "fr" else "Recommendations"

    sections_html: list[str] = []
    section_num = 2
    for cat in ordered_cats:
        cat_findings = by_category.get(cat, [])
        if not cat_findings:
            continue
        label = category_labels.get(cat, cat)
        sections_html.append(f'<div class="report-section" id="sect-{cat}">')
        sections_html.append(f'<h2 class="section-title">{section_num}. {escape(label)}</h2>')
        for idx, f in enumerate(sorted(cat_findings, key=lambda x: _severity_index(x.get("severity"))), start=1):
            block = _build_finding_block(
                f,
                section_num,
                idx,
                severity_label,
                contexte_label,
                impact_label,
                matrice_label,
                risque_label,
                conseils_label,
                include_matrices,
                lang,
            )
            sections_html.append(block)
        sections_html.append("</div>")
        section_num += 1
    return sections_html


def _build_html(
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
    title = "Rapport de scan" if lang == "fr" else "Scan report"
    severity_label = "Sévérité" if lang == "fr" else "Severity"
    disclaimer = (
        "Ce rapport est généré par SecureOps. Usage autorisé uniquement sur des sites dont vous avez la permission."
        if lang == "fr"
        else "This report is generated by SecureOps. Use only on sites you are authorized to scan."
    )

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y %H:%M") if lang == "fr" else dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        date_str = timestamp

    score_val = score or 0
    score_color = "#10b981" if score_val >= 80 else "#f59e0b" if score_val >= 50 else "#ef4444"
    report_title = "Rapport de scan de posture sécurité" if lang == "fr" else "Security Posture Scan Report"
    subtitle = (
        "Analyse non intrusive — TLS, headers, cookies, exposition" if lang == "fr" else "Non-intrusive analysis — TLS, headers, cookies, exposure"
    )

    by_category, ordered_cats = _group_findings_by_category(findings, lang)
    category_labels = _CATEGORY_LABELS_FR if lang == "fr" else _CATEGORY_LABELS_EN

    cover_page = _build_cover_page(url, date_str, lang, report_title, subtitle)
    sommaire_html = _build_sommaire(by_category, ordered_cats, category_labels, lang)
    synthese_html = _build_synthese(by_category, ordered_cats, category_labels, findings, score_val, score_color, lang)
    sections_html = _build_category_sections(by_category, ordered_cats, category_labels, severity_label, include_matrices, lang)

    section_num = 2 + sum(1 for c in ordered_cats if by_category.get(c))
    annexes_label = "Annexes" if lang == "fr" else "Appendix"
    annexes_html = f"""
    <div class="report-section" id="annexes">
        <h2 class="section-title">{section_num}. {annexes_label}</h2>
        <p class="annexes-text">{disclaimer}</p>
    </div>
    """

    return f"""
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{title} - SecureOps</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
            @bottom-right {{
                content: counter(page) " / " counter(pages);
                font-size: 9px;
                color: #94a3b8;
            }}
        }}
        @page :first {{
            margin: 0;
            @bottom-right {{
                content: none;
            }}
        }}
        body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; margin: 0; color: #1f2937; }}
        .cover-page {{
            min-height: 297mm;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 48px;
            box-sizing: border-box;
        }}
        .cover-content {{
            text-align: center;
            max-width: 520px;
            z-index: 1;
        }}
        .cover-logo-top {{
            margin-bottom: 32px;
        }}
        .cover-logo-img {{
            height: 56px;
            width: auto;
            max-width: 180px;
            object-fit: contain;
        }}
        .cover-logo-svg {{
            display: inline-block;
        }}
        .cover-logo-svg svg {{
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}
        .cover-brand {{
            margin-bottom: 48px;
        }}
        .cover-logo {{
            display: block;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #1e40af;
        }}
        .cover-tagline {{
            display: block;
            font-size: 11px;
            font-weight: 400;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6b7280;
            margin-top: 6px;
        }}
        .cover-title {{
            font-size: 22px;
            font-weight: 600;
            line-height: 1.4;
            margin: 0 0 40px 0;
            color: #1f2937;
        }}
        .cover-meta {{
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 32px;
            text-align: left;
        }}
        .cover-meta-row {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .cover-meta-inline {{
            flex-direction: row;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }}
        .cover-meta-sep {{
            color: #9ca3af;
            font-size: 12px;
        }}
        .cover-meta-label {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7280;
        }}
        .cover-meta-value {{
            font-size: 13px;
            color: #374151;
            word-break: break-all;
        }}
        .report-body {{
            padding: 32px 40px;
        }}
        footer {{ margin-top: 32px; font-size: 10px; color: #9ca3af; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
        .report-section {{ margin-bottom: 28px; page-break-inside: avoid; }}
        .report-section:not(.sommaire) {{ page-break-before: always; }}
        .sommaire {{ margin-bottom: 32px; }}
        .section-title {{
            font-size: 22px; font-weight: 600; color: #1e40af;
            margin: 0 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;
        }}
        .subsection-title {{ font-size: 15px; font-weight: 600; color: #374151; margin: 16px 0 8px 0; }}
        .toc-list {{ margin: 0; padding-left: 24px; list-style: none; }}
        .toc-item {{ display: flex; align-items: baseline; margin: 36px 0; font-size: 15px; line-height: 1.5; color: #374151; }}
        .toc-link {{ color: inherit; text-decoration: none; display: flex; align-items: baseline; }}
        .toc-link:hover {{ text-decoration: underline; color: #1e40af; }}
        .toc-num {{ font-weight: 600; font-size: 15px; color: #1e40af; margin-right: 12px; min-width: 24px; }}
        .synthese-gauge-block {{ display: flex; flex-direction: column; align-items: center; margin: 20px 0 24px 0; }}
        .synthese-gauge-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-bottom: 12px; }}
        .synthese-gauge-wrapper {{ position: relative; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; }}
        .synthese-gauge {{ position: absolute; width: 100%; height: 100%; }}
        .synthese-gauge-value {{ position: relative; z-index: 1; font-size: 36px; font-weight: 700; }}
        .synthese-anomalies-block {{ display: flex; flex-direction: column; align-items: center; margin-bottom: 24px; }}
        .synthese-anomalies-value {{ font-size: 28px; font-weight: 700; color: #1f2937; }}
        .synthese-anomalies-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-top: 4px; }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
        .data-table th, .data-table td {{ padding: 8px 12px; text-align: left; border: 1px solid #e5e7eb; }}
        .data-table th {{ background: #f8fafc; font-weight: 600; color: #475569; }}
        .tbl-num {{ text-align: right; font-weight: 500; }}
        .status-ok {{ color: #10b981; font-weight: 600; }}
        .status-fail {{ color: #ef4444; font-weight: 600; }}
        .finding-block {{
            margin: 20px 0; padding: 18px 0; border-bottom: 1px solid #e5e7eb;
            page-break-inside: avoid;
        }}
        .finding-header {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }}
        .finding-title {{ font-size: 13px; font-weight: 600; margin: 0; color: #1e40af; }}
        .finding-badge {{
            display: inline-block; padding: 3px 10px; border-radius: 9999px;
            font-size: 10px; font-weight: 500;
        }}
        .finding-contexte, .finding-impact, .finding-conseils {{
            margin: 10px 0; font-size: 12px; line-height: 1.55; color: #374151;
        }}
        .finding-contexte strong, .finding-impact strong, .finding-conseils strong {{
            font-size: 11px; font-weight: 600; color: #475569;
        }}
        .finding-matrice-label {{ margin: 12px 0 6px 0; font-size: 11px; font-weight: 600; color: #475569; }}
        .finding-matrix {{ margin-top: 8px; }}
        .finding-risque-label {{ margin-top: 10px; font-size: 12px; font-weight: 600; color: #374151; }}
        .annexes-text {{ font-size: 11px; color: #6b7280; line-height: 1.5; }}
    </style>
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
            <p>https://secureops.example.com</p>
        </footer>
    </div>
</body>
</html>
"""


def generate_pdf(
    url: str,
    score: int | None,
    timestamp: str,
    duration: float,
    findings: list[dict[str, Any]],
    include_matrices: bool = True,
    lang: str = "fr",
) -> bytes:
    """Génère le PDF du rapport de scan.

    Args:
        url: URL scannée.
        score: Score /100.
        timestamp: Horodatage ISO.
        duration: Durée en secondes.
        findings: Liste des findings.
        include_matrices: Inclure les matrices gravité/vraisemblance par finding.
        lang: Code langue (fr/en).

    Returns:
        bytes: Contenu binaire du PDF.
    """
    html_content = _build_html(
        url=url,
        score=score,
        timestamp=timestamp,
        duration=duration,
        findings=findings,
        include_matrices=include_matrices,
        lang=lang,
    )
    buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(buffer)
    return buffer.getvalue()
