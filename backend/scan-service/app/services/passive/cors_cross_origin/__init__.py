"""Vérifications CORS et cross-origin (roadmap §5.4).

Référence : docs/verifications/cors-et-cross-origin.md.

- CORS : requêtes GET et OPTIONS avec en-tête Origin sur la page principale et sur des
  URLs dérivées (chemins sensibles). Détection ACAO *, Credentials + réflexion,
  Allow-Methods, Expose-Headers sensibles.
- Mixed content : ressources chargées en HTTP sur page HTTPS (sous-ressources du HTML).
- CORP : Cross-Origin-Resource-Policy manquant.
- Referrer-Policy : vérifié dans la catégorie Security Headers ; mention dans le
  résumé CORS que cette vérification est faite côté headers.
"""

from app.services.passive.cors_cross_origin.checks import CorsCrossOriginCheckResult, run_cors_cross_origin_checks

__all__ = ["CorsCrossOriginCheckResult", "run_cors_cross_origin_checks"]
