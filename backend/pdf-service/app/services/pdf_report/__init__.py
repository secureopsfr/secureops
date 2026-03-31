"""Génération de rapports PDF pour les scans de posture sécurité.

Module découpé : cover, sommaire, synthese, findings, matrix, links, pdf_i18n.
"""

import io

from weasyprint import HTML

from app.schemas.finding import Finding
from app.services.pdf_report.html_builder import build_html


def generate_pdf(
    url: str,
    score: int | None,
    timestamp: str,
    duration: float,
    findings: list[Finding],
    result_mode: str | None = None,
    page_results: list[dict] | None = None,
    include_matrices: bool = True,
    lang: str = "fr",
    scan_mode: str = "passive",
) -> bytes:
    """Génère le PDF du rapport de scan.

    Args:
        url: URL scannée.
        score: Score /100.
        timestamp: Horodatage ISO.
        duration: Durée en secondes.
        findings: Liste des findings validés.
        result_mode: Mode de résultat (single/multi), optionnel.
        page_results: Résultats par page en mode multi, optionnel.
        include_matrices: Inclure les matrices gravité/vraisemblance par finding.
        lang: Code langue (fr/en).
        scan_mode: Mode de scan (passive, intrusive, custom).

    Returns:
        bytes: Contenu binaire du PDF.
    """
    html_content = build_html(
        url=url,
        score=score,
        timestamp=timestamp,
        duration=duration,
        findings=findings,
        result_mode=result_mode,
        page_results=page_results,
        include_matrices=include_matrices,
        lang=lang,
        scan_mode=scan_mode,
    )
    buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(buffer)
    return buffer.getvalue()
