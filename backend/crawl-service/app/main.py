"""Point d'entrée principal du Crawl Service."""

from contextlib import asynccontextmanager

from common.error_handlers import register_exception_handlers
from common.logging_config import get_logger, setup_logging
from common.middleware import CorrelationIdMiddleware
from common.version import get_app_version
from fastapi import FastAPI

from app.load_env import ensure_env_loaded

ensure_env_loaded()

setup_logging(service_name="crawl-service")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown)."""
    from app.db import init_db

    logger.info("Démarrage du Crawl Service")
    try:
        initialized = await init_db()
        if initialized:
            logger.info("Base de données crawl-service initialisée")
        else:
            logger.warning("DATABASE_URL absente: endpoints async crawl indisponibles")
    except Exception as exc:
        logger.warning("Init DB crawl-service échouée: %s", exc)
    yield
    logger.info("Arrêt du Crawl Service")


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI.

    Returns:
        FastAPI: application configurée.
    """
    from app.config_loader import settings
    from app.routers.crawl import router as crawl_router
    from app.routers.health import router as health_router

    config = settings()
    app = FastAPI(title=config.general.service_name, version=get_app_version(), lifespan=lifespan)

    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(health_router)
    app.include_router(crawl_router)
    register_exception_handlers(app)

    return app


app = create_app()
