"""Validation et normalisation des URLs pour le scan (posture sécurité).

Conformité roadmap MVP : schéma http/https uniquement, pas de credentials,
ports 80/443, longueur limitée, normalisation. Configuration dans config/settings.yml (url_validation).
"""

from urllib.parse import urlparse, urlunparse

from app.config_loader import get_url_validation_settings


class URLValidationError(ValueError):
    """Erreur de validation d'URL (schéma, credentials, port, longueur)."""

    pass


def validate_and_normalize_url(url: str) -> str:
    """Valide l'URL et retourne une forme normalisée.

    Vérifications (roadmap §2.1) :
    - Schéma http ou https uniquement.
    - Refus des credentials (user:pass@host).
    - Port 80, 443 ou port par défaut implicite.
    - Longueur <= max_url_length (settings).
    - Normalisation (minuscules schéma/netloc, fragment supprimé).

    Args:
        url: Chaîne URL à valider.

    Returns:
        str: URL normalisée (sans fragment, schéma/netloc en minuscules).

    Raises:
        URLValidationError: Si l'URL est invalide (schéma, credentials, port, longueur).
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL vide ou invalide.")

    cfg = get_url_validation_settings()
    url_stripped = url.strip()
    if len(url_stripped) > cfg.max_url_length:
        raise URLValidationError(f"URL trop longue (max {cfg.max_url_length} caractères).")

    try:
        parsed = urlparse(url_stripped)
    except Exception as e:
        raise URLValidationError(f"URL mal formée: {e}") from e

    scheme = (parsed.scheme or "").lower()
    if scheme not in cfg.allowed_schemes:
        raise URLValidationError(f"Seuls les schémas http et https sont autorisés (reçu: {parsed.scheme or 'vide'}).")

    if parsed.username or parsed.password:
        raise URLValidationError("Les credentials dans l'URL (user:pass@host) ne sont pas autorisés.")

    if parsed.port is not None and parsed.port not in cfg.allowed_ports:
        raise URLValidationError("Seuls les ports 80 et 443 sont autorisés.")

    if not parsed.netloc:
        raise URLValidationError("URL sans host (netloc manquant).")

    # Normalisation : minuscules pour schéma et netloc, suppression du fragment
    normalized_netloc = parsed.netloc.lower()
    normalized = urlunparse((scheme, normalized_netloc, parsed.path or "/", parsed.params, parsed.query, ""))
    if len(normalized) > cfg.max_url_length:
        raise URLValidationError(f"URL normalisée trop longue (max {cfg.max_url_length} caractères).")

    return normalized
