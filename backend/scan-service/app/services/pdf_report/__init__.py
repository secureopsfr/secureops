"""Génération de rapports PDF pour les scans de posture sécurité.

Module découpé : cover, sommaire, synthese, findings, matrix, links, pdf_i18n.
"""

import io
from typing import Any

from weasyprint import HTML

from app.services.pdf_report.html_builder import build_html


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
    html_content = build_html(
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
