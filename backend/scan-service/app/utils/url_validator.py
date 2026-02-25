"""Validation et normalisation des URLs pour le scan (posture sécurité).

Conformité roadmap MVP : schéma http/https uniquement, pas de credentials,
ports 80/443, longueur limitée, normalisation.
"""

from urllib.parse import urlparse, urlunparse

# Longueur maximale d'URL (anti-abus).
MAX_URL_LENGTH = 2048

# Schémas autorisés (scanner web uniquement).
ALLOWED_SCHEMES = ("http", "https")

# Ports autorisés (80 et 443 ; None = port par défaut implicite).
ALLOWED_PORTS = (80, 443, None)


class URLValidationError(ValueError):
    """Erreur de validation d'URL (schéma, credentials, port, longueur)."""

    pass


def validate_and_normalize_url(url: str) -> str:
    """Valide l'URL et retourne une forme normalisée.

    Vérifications (roadmap §2.1) :
    - Schéma http ou https uniquement.
    - Refus des credentials (user:pass@host).
    - Port 80, 443 ou port par défaut implicite.
    - Longueur <= MAX_URL_LENGTH.
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

    url_stripped = url.strip()
    if len(url_stripped) > MAX_URL_LENGTH:
        raise URLValidationError(f"URL trop longue (max {MAX_URL_LENGTH} caractères).")

    try:
        parsed = urlparse(url_stripped)
    except Exception as e:
        raise URLValidationError(f"URL mal formée: {e}") from e

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise URLValidationError(f"Seuls les schémas http et https sont autorisés (reçu: {parsed.scheme or 'vide'}).")

    if parsed.username or parsed.password:
        raise URLValidationError("Les credentials dans l'URL (user:pass@host) ne sont pas autorisés.")

    if parsed.port is not None and parsed.port not in (80, 443):
        raise URLValidationError("Seuls les ports 80 et 443 sont autorisés.")

    if not parsed.netloc:
        raise URLValidationError("URL sans host (netloc manquant).")

    # Normalisation : minuscules pour schéma et netloc, suppression du fragment
    normalized_netloc = parsed.netloc.lower()
    normalized = urlunparse((scheme, normalized_netloc, parsed.path or "/", parsed.params, parsed.query, ""))
    if len(normalized) > MAX_URL_LENGTH:
        raise URLValidationError(f"URL normalisée trop longue (max {MAX_URL_LENGTH} caractères).")

    return normalized
