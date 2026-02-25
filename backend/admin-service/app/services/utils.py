"""Utilitaires partagés entre les modules de services."""


def auto_bucket_minutes(window_minutes: int) -> int:
    """Calcule automatiquement la taille des buckets selon la fenêtre temporelle.

    Vise environ 60-120 points pour une bonne lisibilité des graphiques.

    Args:
        window_minutes: fenêtre temporelle totale en minutes.

    Returns:
        int: taille du bucket en minutes.
    """
    if window_minutes <= 60:
        return 1
    if window_minutes <= 360:
        return 5
    if window_minutes <= 1440:
        return 15
    if window_minutes <= 10080:
        return 60
    if window_minutes <= 43200:
        return 360
    return 1440
