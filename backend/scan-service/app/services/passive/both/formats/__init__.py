"""Vérifications des formats de réponse (Content-Type, X-CTO, compression).

Périmètre : les deux (frontend et backend).
"""

from app.services.passive.both.formats.checks import FormatsCheckResult, FormatsIssue, check_formats_from_response

__all__ = ["FormatsCheckResult", "FormatsIssue", "check_formats_from_response"]
