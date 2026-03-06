"""Lecture de la version applicative depuis le fichier VERSION à la racine du projet.

Source unique de vérité pour la version affichée dans les APIs (FastAPI, OpenAPI).
"""

from pathlib import Path


def get_app_version() -> str:
    """Lit la version depuis le fichier VERSION à la racine du projet.

    Returns:
        str: Version (ex. "0.2.0"). Retourne "0.0.0" si le fichier est absent.
    """
    # common/version.py → backend/common/common/ → racine = parents[3]
    _root = Path(__file__).resolve().parents[3]
    _version_file = _root / "VERSION"
    if _version_file.exists():
        return _version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"
