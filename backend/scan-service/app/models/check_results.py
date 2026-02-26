"""Interface commune pour les résultats de vérification du scan."""

from typing import Protocol


class CheckResultProtocol(Protocol):
    """Protocole commun pour les résultats de vérification (headers, cookies, TLS, exposed_files).

    Tous les résultats exposent findings, fetch_ok et to_dict() pour une exploitation
    uniforme dans le flux SSE.
    """

    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise le résultat pour l'événement SSE result."""
        ...
