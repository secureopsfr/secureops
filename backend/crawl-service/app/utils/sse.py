"""Utilitaires pour le format Server-Sent Events (SSE)."""

import json


def sse_message(event: str, data: dict) -> str:
    """Formate un message Server-Sent Events.

    Args:
        event: Nom de l'événement SSE.
        data: Données JSON à envoyer.

    Returns:
        str: Bloc SSE (event + data + double newline).
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
