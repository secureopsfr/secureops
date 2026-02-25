"""Router de santé pour l'API Gateway.

Endpoints pour vérifier l'état de santé du service.
"""

from common.health import create_health_router

router = create_health_router(service_name="API Gateway", prefix="", tags=["health"])
