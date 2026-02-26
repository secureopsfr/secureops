"""Utilitaires pour la manipulation des en-têtes HTTP (accès insensible à la casse)."""

from typing import Any


def get_header_insensitive(response: Any, name: str) -> str | None:
    """Retourne la valeur d'un en-tête HTTP (recherche insensible à la casse).

    Args:
        response: Objet ayant un attribut headers (ex. httpx.Response).
        name: Nom de l'en-tête (ex. "Server", "X-Powered-By").

    Returns:
        str | None: Valeur de l'en-tête ou None si absent.
    """
    headers = response.headers
    name_lower = name.lower()
    # Support style httpx.Headers : itération (k, v) et .get(k) avec clé exacte
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return None
