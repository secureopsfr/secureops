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


# Couleurs de la matrice (docs/verifications)
_COLORS = [
    ["#22c55e", "#22c55e", "#facc15", "#facc15"],  # Mineure
    ["#22c55e", "#facc15", "#f97316", "#f97316"],  # Significative
    ["#facc15", "#f97316", "#ef4444", "#ef4444"],  # Importante
    ["#f97316", "#ef4444", "#ef4444", "#ef4444"],  # Majeure
]
_GRAVITES = ("Mineure", "Significative", "Importante", "Majeure")
_VRAISEMBLANCES = ("Très faible", "Faible", "Forte", "Très forte")


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

    rows = []
    # En-tête
    header_cells = "<th style='border:1px solid #333;padding:6px;font-weight:bold'>Gravité \\ Vraisemblance</th>" + "".join(
        f"<th style='border:1px solid #333;padding:6px;font-weight:bold'>{escape(v)}</th>" for v in _VRAISEMBLANCES
    )
    rows.append(f"<tr>{header_cells}</tr>")

    for i, grav in enumerate(_GRAVITES):
        cells = []
        for j in range(4):
            bg = _COLORS[i][j]
            cross = "✗" if (i == row_idx and j == col_idx) else ""
            style = f"border:1px solid #333;padding:8px;background-color:{bg};min-width:50px;text-align:center"
            cells.append(f"<td style='{style}'>{escape(cross)}</td>")
        row_label = f"<td style='border:1px solid #333;padding:6px;font-weight:bold'>{escape(grav)}</td>"
        rows.append(f"<tr>{row_label}{''.join(cells)}</tr>")

    return f"<table style='border-collapse:collapse;margin:12px 0'>{''.join(rows)}</table>"


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
    score_label = "Score" if lang == "fr" else "Score"
    url_label = "URL scannée" if lang == "fr" else "Scanned URL"
    date_label = "Date" if lang == "fr" else "Date"
    duration_label = "Durée (s)" if lang == "fr" else "Duration (s)"
    findings_label = "Findings" if lang == "fr" else "Findings"
    severity_label = "Sévérité" if lang == "fr" else "Severity"
    evidence_label = "Preuve" if lang == "fr" else "Evidence"
    recommendation_label = "Recommandation" if lang == "fr" else "Recommendation"
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
    # Même logique que scanConstants.getScoreBadge : >= 80 vert, >= 50 jaune, sinon rouge
    score_color = "#10b981" if score_val >= 80 else "#f59e0b" if score_val >= 50 else "#ef4444"

    report_title = "Rapport de scan de posture sécurité" if lang == "fr" else "Security Posture Scan Report"
    subtitle = (
        "Analyse non intrusive — TLS, headers, cookies, exposition" if lang == "fr" else "Non-intrusive analysis — TLS, headers, cookies, exposure"
    )

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")[:60]
    if len(url) > 60:
        display_url += "…"

    # Jauge circulaire : circonférence = 2 * pi * 42 ≈ 263.9
    circumference = 2 * 3.14159 * 42
    stroke_dashoffset = circumference * (1 - score_val / 100)

    logo_data = _get_logo_data_uri()
    logo_html = (
        f'<img src="{logo_data}" alt="SecureOps" class="cover-logo-img" />'
        if logo_data
        else f'<span class="cover-logo-svg">{_LOGO_SVG_FALLBACK}</span>'
    )

    cover_page = f"""
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
            <div class="cover-score-block">
                <span class="cover-score-label">{score_label}</span>
                <div class="cover-gauge-wrapper">
                    <svg class="cover-gauge" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(148,163,184,0.3)" stroke-width="8"/>
                        <circle cx="50" cy="50" r="42" fill="none" stroke="{score_color}" stroke-width="8" stroke-linecap="round"
                                stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
                                transform="rotate(-90 50 50)"/>
                    </svg>
                    <span class="cover-score-value" style="color:{score_color}">{score_val}</span>
                </div>
            </div>
            <div class="cover-footer">
                <span class="cover-footer-count">{len(findings)}</span>
                <span class="cover-footer-label">{"anomalies détectées" if lang == "fr" else "findings detected"}</span>
            </div>
        </div>
    </div>
    """

    findings_html = []
    for f in findings:
        slug = f.get("id", "")
        title_f = escape(str(f.get("title", "")))
        severity = escape(str(f.get("severity", "")))
        evidence = escape(str(f.get("evidence", ""))[:500])
        recommendation = escape(str(f.get("recommendation", ""))[:500])

        block = f"""
        <div style='margin:16px 0;padding:12px;border:1px solid #ddd;border-radius:6px'>
            <h3 style='margin:0 0 8px 0;font-size:14px'>{title_f}</h3>
            <p style='margin:4px 0'><strong>{severity_label}:</strong> {severity}</p>
            <p style='margin:4px 0'><strong>{evidence_label}:</strong> {evidence}</p>
            <p style='margin:4px 0'><strong>{recommendation_label}:</strong> {recommendation}</p>
        """
        if include_matrices and slug:
            gravite = get_gravite(slug)
            vraisemblance = get_vraisemblance(slug)
            block += _render_matrix(gravite, vraisemblance)
        block += "</div>"
        findings_html.append(block)

    findings_section = (
        "".join(findings_html) if findings_html else ("<p>Aucun finding détecté.</p>" if lang == "fr" else "<p>No findings detected.</p>")
    )

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
        .cover-score-block {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            margin-bottom: 40px;
        }}
        .cover-score-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7280;
        }}
        .cover-gauge-wrapper {{
            position: relative;
            width: 120px;
            height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .cover-gauge {{
            position: absolute;
            width: 100%;
            height: 100%;
        }}
        .cover-score-value {{
            position: relative;
            z-index: 1;
            font-size: 36px;
            font-weight: 700;
        }}
        .cover-footer {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        .cover-footer-count {{
            font-size: 32px;
            font-weight: 700;
            color: #1f2937;
        }}
        .cover-footer-label {{
            font-size: 11px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .report-body {{
            padding: 32px 40px;
        }}
        .header {{ margin-bottom: 24px; }}
        h1 {{ font-size: 18px; margin-bottom: 8px; color: #1f2937; }}
        .score {{ font-size: 24px; margin: 8px 0; }}
        .meta {{ font-size: 12px; color: #6b7280; }}
        footer {{ margin-top: 32px; font-size: 10px; color: #9ca3af; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
    {cover_page}
    <div class="report-body">
        <div class="header">
            <h1>SecureOps — {title}</h1>
            <p class="meta">{url_label}: {escape(url)}</p>
            <p class="meta">{date_label}: {date_str} | {duration_label}: {duration:.1f}</p>
            <p class="score">{score_label}: {score or 0}/100</p>
        </div>
        <h2 style="font-size:16px; color:#374151">{findings_label}</h2>
        {findings_section}
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
