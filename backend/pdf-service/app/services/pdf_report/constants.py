"""Constantes partagées pour le rendu du rapport PDF."""

SEVERITY_LIST = ["critical", "high", "medium", "low", "info"]
SEVERITY_ORDER: dict[str, int] = {s: i for i, s in enumerate(SEVERITY_LIST)}


def severity_index(severity: str) -> int:
    """Retourne l'index de tri pour la sévérité (critical=0, info=4)."""
    s = (severity or "info").lower()
    return SEVERITY_ORDER.get(s, 99)
