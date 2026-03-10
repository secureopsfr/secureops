"""Middlewares communs pour les micro-services FastAPI.

Fournit :
- ``CorrelationIdMiddleware`` : génère ou propage un *correlation_id*
  unique par requête, injecté dans les logs et renvoyé dans les headers.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from common.logging_config import correlation_id_ctx

# Nom du header HTTP pour le correlation ID
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware qui attache un correlation_id à chaque requête.

    Si le header ``X-Correlation-ID`` est présent dans la requête entrante,
    il est réutilisé (propagation cross-service). Sinon, un UUID v4 est généré.

    Le correlation_id est :
    - stocké dans un ``ContextVar`` pour être accessible dans les logs ;
    - renvoyé dans le header de réponse ``X-Correlation-ID``.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Traite la requête en injectant le correlation_id.

        Args:
            request: requête HTTP entrante.
            call_next: prochain middleware / handler.

        Returns:
            Response: réponse HTTP avec le header ``X-Correlation-ID``.
        """
        # Récupérer ou générer le correlation_id
        cid = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # Stocker dans le ContextVar (disponible pour les loggers)
        token = correlation_id_ctx.set(cid)

        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = cid
            return response
        finally:
            # Remettre le ContextVar à sa valeur précédente
            correlation_id_ctx.reset(token)
