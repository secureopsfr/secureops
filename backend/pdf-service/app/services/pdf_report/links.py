"""Construction des liens externes pour le rapport PDF."""

from html import escape


def build_ref_links(
    references: list[str],
    max_count: int = 10,
) -> str:
    """Construit le HTML d'une liste de liens (ul/li) pour les références."""
    if not references:
        return ""
    refs = references[:max_count]
    items = [f'<li><a href="{escape(ref)}" target="_blank" rel="noopener noreferrer">{escape(ref)}</a></li>' for ref in refs]
    return '<ul class="finding-refs">' + "".join(items) + "</ul>"


def build_inline_ref_links(
    references: list[str],
    max_count: int = 3,
    prefix: str = "",
) -> str:
    """Construit le HTML de liens inline pour « En savoir plus »."""
    if not references:
        return ""
    refs = references[:max_count]
    links = [f'<a href="{escape(ref)}" class="finding-detail-link" target="_blank" rel="noopener noreferrer">{escape(ref)}</a>' for ref in refs]
    return f'<p class="finding-detail-refs">{prefix} {" ".join(links)}</p>'
