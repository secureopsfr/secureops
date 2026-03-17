"""Mapping OWASP Top 10:2025 par slug de finding.

Charge owasp_mapping.json. Pas de fallback : slugs non mappés retournent ().
Support des préfixes pour les slugs dynamiques (ex. exposed_files-.env → exposed_files).
"""

import json
from functools import lru_cache
from pathlib import Path


def _load_mapping() -> dict[str, list[str]]:
    """Charge le mapping depuis owasp_mapping.json."""
    path = Path(__file__).resolve().parent / "owasp_mapping.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    # Exclure _meta et autres clés non-slug
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, list)}


@lru_cache(maxsize=1)
def _get_mapping() -> dict[str, list[str]]:
    """Retourne le mapping (mis en cache)."""
    return _load_mapping()


def get_owasp_categories(slug: str) -> tuple[str, ...]:
    """Retourne les catégories OWASP pour un slug.

    Essai 1 : correspondance exacte.
    Essai 2 : préfixe (slug exposé_files-xxx → mapping exposed_files).

    Args:
        slug: Identifiant du finding (ex. tls-https-disabled, exposed_files-.env).

    Returns:
        tuple[str, ...]: Codes OWASP (A01, A02, ...) ou () si non mappé.
    """
    mapping = _get_mapping()
    categories = mapping.get(slug)
    if categories is not None:
        return tuple(str(c) for c in categories)
    # Préfixe pour slugs dynamiques (exposed_files-.env, directory_listing-uploads)
    if "-" in slug:
        prefix = slug.split("-", 1)[0]
        prefix_cats = mapping.get(prefix)
        if prefix_cats is not None:
            return tuple(str(c) for c in prefix_cats)
    return ()
