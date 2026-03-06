"""Configuration des vérifications Information disclosure (roadmap §5.2).

Cette configuration contrôle principalement la limite de taille des corps de
réponse analysés pour éviter les scans trop coûteux en mémoire/CPU.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class InformationDisclosureSettings:
    """Configuration pour les vérifications de fuites d'information.

    Attributes:
        max_body_bytes (int): Nombre maximal d'octets du corps de réponse à
            analyser pour rechercher des fuites (stack traces, secrets, etc.).
    """

    max_body_bytes: int


_DEFAULT_MAX_BODY_BYTES = 1_048_576


@lru_cache(maxsize=1)
def get_information_disclosure_settings() -> InformationDisclosureSettings:
    """Charge la section information_disclosure depuis config/settings.yml.

    Returns:
        InformationDisclosureSettings: Configuration normalisée pour les
        vérifications de fuites d'information.
    """
    data = _load_settings_yml()
    raw = data.get("information_disclosure") or {}
    max_body_bytes = int(raw.get("max_body_bytes", _DEFAULT_MAX_BODY_BYTES))
    return InformationDisclosureSettings(max_body_bytes=max_body_bytes)


@lru_cache(maxsize=1)
def get_information_disclosure_max_body() -> int:
    """Retourne la limite de lecture du corps pour information_disclosure.

    Returns:
        int: Nombre maximal d'octets à analyser dans le corps de réponse.
    """
    return get_information_disclosure_settings().max_body_bytes
