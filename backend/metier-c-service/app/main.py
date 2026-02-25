"""Point d'entrée principal du Metier C Service."""

from contextlib import asynccontextmanager

from common.error_handlers import register_exception_handlers
from common.logging_config import get_logger, setup_logging
from common.middleware import CorrelationIdMiddleware
from fastapi import FastAPI

from app.config_loader import settings
from app.routers.health import router as health_router

setup_logging(service_name="metier-c-service")

config = settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown)."""
    # Startup
    logger.info("Démarrage du Metier C Service")
    yield
    # Shutdown
    logger.info("Arrêt du Metier C Service")


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI.

    Returns:
        FastAPI: application configurée.
    """
    app = FastAPI(title=config.general.service_name, version="0.1.0", lifespan=lifespan)

    # Pas de CORS : ce service est interne, seul le gateway y accède.
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(health_router)
    register_exception_handlers(app)

    return app


app = create_app()
