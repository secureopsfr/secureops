"""Route de santé pour le Metier A Service."""

from common.health import create_health_router

from app.config_loader import settings

config = settings()
router_config = config.routers.health
router = create_health_router(
    service_name=config.general.service_name,
    prefix=router_config.prefix,
    tags=router_config.tags,
)
