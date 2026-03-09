"""Détection des protections anti-bot dans le HTML."""


def detect_anti_bot(html: str, indicators: tuple[str, ...]) -> bool:
    """Détecte si le HTML contient des indicateurs de protection anti-bot.

    Args:
        html: Contenu HTML de la page.
        indicators: Tuple de chaînes caractéristiques (ex. cloudflare, captcha).

    Returns:
        True si au moins un indicateur est trouvé.
    """
    if not html or len(html) < 100:
        return False
    lower = html.lower()
    return any(indicator in lower for indicator in indicators)
