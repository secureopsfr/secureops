"""Page de garde du rapport PDF."""

import base64
import os
from html import escape
from pathlib import Path

from app.services.pdf_report.pdf_i18n import t

_DEFAULT_LOGO_PATH = Path(__file__).resolve().parents[2] / "static" / "logo.png"
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


def build_cover_page(
    url: str,
    date_str: str,
    lang: str,
    report_title: str,
    subtitle: str,
) -> str:
    """Construit le HTML de la page de garde."""
    url_label = t("cover_url_label", lang)
    date_label = t("cover_date_label", lang)
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
