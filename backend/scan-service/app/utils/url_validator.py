"""Validation et normalisation des URLs pour le scan (posture sécurité).

Délègue à common.url_utils pour la normalisation de base, puis ajoute
la validation des ports (config settings.yml).
"""

from urllib.parse import urlparse

from common.url_utils import URLValidationError, normalize_scan_url

from app.config_loader import get_url_validation_settings


def validate_and_normalize_url(url: str) -> str:
    """Valide l'URL et retourne une forme normalisée.

    Utilise common.url_utils pour schéma, credentials, netloc. Ajoute
    la validation des ports (80, 443, 1010, 1011 selon config).

    Args:
        url: Chaîne URL à valider.

    Returns:
        str: URL normalisée.

    Raises:
        URLValidationError: Si l'URL est invalide.
    """
    cfg = get_url_validation_settings()
    normalized = normalize_scan_url(url, max_length=cfg.max_url_length)

    parsed = urlparse(normalized)
    if parsed.port is not None and parsed.port not in cfg.allowed_ports:
        ports_str = ", ".join(str(p) for p in sorted(cfg.allowed_ports))
        raise URLValidationError(f"Seuls les ports {ports_str} sont autorisés.")

    return normalized
