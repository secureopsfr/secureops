"""Point d'entrée principal du User Service."""

from contextlib import asynccontextmanager

from common.error_handlers import register_exception_handlers
from common.logging_config import get_logger, setup_logging
from common.middleware import CorrelationIdMiddleware
from fastapi import FastAPI

from app.config_loader import settings
from app.db import init_db
from app.routers.favorites import router as favorites_router
from app.routers.health import router as health_router
from app.routers.preferences import router as preferences_router
from app.routers.privacy import router as privacy_router
from app.routers.profile import router as profile_router
from app.routers.scan_history import router as scan_history_router
from app.routers.security import router as security_router
from app.routers.subscription import router as subscription_router

setup_logging(service_name="user-service")

config = settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown)."""
    # Startup: initialiser la base de données
    await init_db()
    yield
    # Shutdown: rien à faire pour l'instant


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI.

    Returns:
        FastAPI: application configurée.
    """
    app = FastAPI(title=config.general.service_name, version="0.1.0", lifespan=lifespan)

    # Pas de CORS : ce service est interne, seul le gateway y accède.
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(health_router)
    app.include_router(profile_router)
    app.include_router(security_router)
    app.include_router(favorites_router)
    app.include_router(scan_history_router)
    app.include_router(subscription_router)
    app.include_router(preferences_router)
    app.include_router(privacy_router)
    register_exception_handlers(app)

    return app


app = create_app()
