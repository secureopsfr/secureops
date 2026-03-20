"""Vérifications d'intégrité et de sous-ressources (SRI + HTML).

Ce package expose les types et la fonction de haut niveau utilisés par la
pipeline de scan pour analyser :

- l'utilisation de Subresource Integrity (SRI) sur les scripts/CSS externes ;
- certaines bonnes pratiques HTML (scripts inline vs CSP, formulaires, liens,
  meta robots) décrites dans
  ``docs/verifications/integrite-et-sous-ressources.md``.
"""

from app.services.passive.frontend.integrity.checks import IntegrityCheckResult, check_integrity_from_response

__all__ = ["IntegrityCheckResult", "check_integrity_from_response"]
