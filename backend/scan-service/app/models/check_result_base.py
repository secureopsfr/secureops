"""Protocole commun pour les résultats de checks (fetch_ok, to_dict).

Tous les CheckResult (TlsCheckResult, SecurityHeadersCheckResult, etc.) partagent
fetch_ok et to_dict(). Ce protocole documente l'interface pour le typage.
"""

from typing import Protocol


class CheckResultProtocol(Protocol):
    """Protocole pour les résultats de checks (structural typing).

    Toute classe avec fetch_ok et to_dict() conforme à ce protocole.
    """

    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        ...
