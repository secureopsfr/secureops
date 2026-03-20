"""Vérifications Méthodes HTTP et redirections (ex-roadmap 5.5).

Réutilise les réponses OPTIONS du module CORS (Allow, Access-Control-Allow-Methods).
Effectue des requêtes TRACE (XST), HEAD, et analyse les chaînes de redirection.
Référence : docs/verifications/passive/methodes-http-et-redirections.md
"""

from app.services.passive.both.methodes_http_et_redirections.checks import MethodesHttpCheckResult, run_methodes_http_checks

__all__ = ["MethodesHttpCheckResult", "run_methodes_http_checks"]
