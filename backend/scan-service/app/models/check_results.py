"""Interface commune pour les résultats de vérification du scan."""

from typing import Protocol


class CheckResultProtocol(Protocol):
    """Protocole commun pour les résultats de vérification (headers, cookies, TLS).

    Tous les résultats exposent findings et fetch_ok pour une exploitation uniforme
    dans le flux SSE.
    """

    findings: tuple[str, ...]
    fetch_ok: bool
