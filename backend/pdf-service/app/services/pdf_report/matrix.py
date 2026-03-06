"""Matrice gravité/vraisemblance pour les findings (rapport PDF)."""

from html import escape

from app.services.pdf_report.pdf_i18n import t, translate_gravite, translate_vraisemblance

_COLORS = [
    ["#22c55e", "#22c55e", "#facc15", "#facc15"],
    ["#22c55e", "#facc15", "#f97316", "#f97316"],
    ["#facc15", "#f97316", "#ef4444", "#ef4444"],
    ["#f97316", "#ef4444", "#ef4444", "#ef4444"],
]
_GRAVITES_FR = ("Mineure", "Significative", "Importante", "Majeure")
_VRAISEMBLANCES_FR = ("Très faible", "Faible", "Forte", "Très forte")


def _gravite_index(gravite: str) -> int:
    """Retourne l'index de ligne pour la gravité."""
    try:
        return _GRAVITES_FR.index(gravite)
    except ValueError:
        return 1


def _vraisemblance_index(vraisemblance: str) -> int:
    """Retourne l'index de colonne pour la vraisemblance."""
    try:
        return _VRAISEMBLANCES_FR.index(vraisemblance)
    except ValueError:
        return 2


def render_matrix(gravite: str, vraisemblance: str, lang: str) -> str:
    """Génère le HTML d'une matrice avec croix à la position (gravité, vraisemblance)."""
    row_idx = _gravite_index(gravite)
    col_idx = _vraisemblance_index(vraisemblance)

    cell_size = "width:70px;height:38px;box-sizing:border-box"
    th_style = f"border:1px solid #333;padding:4px 6px;font-weight:600;font-size:9px;text-align:center;{cell_size}"
    td_style = f"border:1px solid #333;padding:6px;text-align:center;font-size:10px;{cell_size}"

    header_label = t("matrix_gravite", lang)
    header_cells = f"<th style='{th_style}'>{escape(header_label)}</th>" + "".join(
        f"<th style='{th_style}'>{escape(translate_vraisemblance(v, lang))}</th>" for v in _VRAISEMBLANCES_FR
    )
    rows = [f"<tr>{header_cells}</tr>"]

    for i, grav in enumerate(_GRAVITES_FR):
        cells = []
        for j in range(4):
            bg = _COLORS[i][j]
            cross = "×" if (i == row_idx and j == col_idx) else ""
            style = f"{td_style};background-color:{bg}"
            cross_html = f'<span style="font-size:18px;font-weight:700">{escape(cross)}</span>' if cross else ""
            cells.append(f"<td style='{style}'>{cross_html}</td>")
        row_label = f"<td style='{th_style}'>{escape(translate_gravite(grav, lang))}</td>"
        rows.append(f"<tr>{row_label}{''.join(cells)}</tr>")

    return f"<table style='border-collapse:collapse;margin:12px 0;table-layout:fixed'>{''.join(rows)}</table>"
