"""Schéma Pydantic d'un finding issu d'un scan de posture sécurité."""

from pydantic import BaseModel, ConfigDict, field_validator


class Finding(BaseModel):
    """Un finding issu d'un scan de posture sécurité."""

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    category: str = "other"
    title: str = ""
    severity: str = "info"
    evidence: str = ""
    recommendation: str = ""
    references: list[str] = []
    owasp_categories: list[str] = []
    # Champs techniques (scans intrusifs)
    request_url: str | None = None
    request_method: str | None = None
    raw_evidence: str | None = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalise_severity(cls, v: object) -> str:
        """Normalise la sévérité en minuscules, fallback sur 'info'."""
        valid = {"critical", "high", "medium", "low", "info"}
        s = str(v or "info").lower()
        return s if s in valid else "info"
