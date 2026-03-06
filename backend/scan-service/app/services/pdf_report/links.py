"""Construction des liens externes pour le rapport PDF.

Factorise la génération HTML des références (target="_blank", rel="noopener noreferrer").
"""

from html import escape


def build_ref_links(
    references: list[str],
    lang: str,
    max_count: int = 10,
) -> str:
    """Construit le HTML d'une liste de liens (ul/li) pour les références.

    Args:
        references: Liste d'URLs.
        lang: Code langue (fr/en) — non utilisé ici, réservé pour libellé.
        max_count: Nombre max de liens à inclure.

    Returns:
        str: Fragment HTML <ul>...</ul> ou chaîne vide si pas de références.
    """
    if not references:
        return ""
    refs = references[:max_count]
    items = [f'<li><a href="{escape(ref)}" target="_blank" rel="noopener noreferrer">{escape(ref)}</a></li>' for ref in refs]
    return '<ul class="finding-refs">' + "".join(items) + "</ul>"


def build_inline_ref_links(
    references: list[str],
    lang: str,
    max_count: int = 3,
    prefix: str = "",
) -> str:
    """Construit le HTML de liens inline (séparés par espaces) pour « En savoir plus ».

    Args:
        references: Liste d'URLs.
        lang: Code langue (fr/en) — non utilisé, réservé.
        max_count: Nombre max de liens.
        prefix: Prefixe avant les liens (ex. "En savoir plus : ").

    Returns:
        str: Fragment HTML ou chaîne vide.
    """
    if not references:
        return ""
    refs = references[:max_count]
    links = [f'<a href="{escape(ref)}" class="finding-detail-link" target="_blank" rel="noopener noreferrer">{escape(ref)}</a>' for ref in refs]
    return f'<p class="finding-detail-refs">{prefix} {" ".join(links)}</p>'
