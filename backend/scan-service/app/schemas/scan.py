"""Schémas de requête et réponse pour l'endpoint de scan."""

from pydantic import BaseModel, Field

from app.config_loader import get_url_validation_settings


class ScanRequest(BaseModel):
    """Corps de requête pour lancer un scan.

    Attributes:
        url: URL à scanner (http ou https).
    """

    url: str = Field(
        ...,
        description="URL à scanner (http ou https)",
        min_length=1,
        max_length=get_url_validation_settings().max_url_length,
    )
