"""Schémas de requête et réponse pour l'endpoint de scan."""

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Corps de requête pour lancer un scan.

    Attributes:
        url: URL à scanner (http ou https).
    """

    url: str = Field(..., description="URL à scanner (http ou https)", min_length=1, max_length=2048)


class ScanValidationResponse(BaseModel):
    """Réponse après validation d'URL (étape actuelle : validation uniquement).

    Attributes:
        valid: Indique que l'URL a passé la validation.
        url: URL normalisée (schéma/netloc en minuscules, fragment supprimé).
    """

    valid: bool = Field(True, description="URL valide pour un scan")
    url: str = Field(..., description="URL normalisée")
