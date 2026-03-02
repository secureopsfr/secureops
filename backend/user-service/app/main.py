"""Point d'entrée principal du User Service."""

import asyncio
import contextlib
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
from app.routers.scheduled_scan import router as scheduled_scan_router
from app.routers.security import router as security_router
from app.routers.subscription import router as subscription_router
from app.services.scheduled_scan_scheduler import scheduled_scan_loop

setup_logging(service_name="user-service")

config = settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown)."""
    max_retries = 5
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Tentative d'initialisation de la base de données (%s/%s)", attempt, max_retries)
            await init_db()
            logger.info("Base de données initialisée avec succès")
            break
        except Exception as e:
            logger.warning("Échec de l'initialisation de la base de données: %s", e)
            logger.exception("Traceback init_db")
            if attempt < max_retries:
                logger.info("Réessai dans %s secondes...", retry_delay)
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Impossible d'initialiser la base de données après tous les essais")
                raise

    # Lancer le scheduler des scans planifiés
    scheduler_task = asyncio.create_task(scheduled_scan_loop())
    logger.info("Scheduler des scans planifiés démarré")

    yield

    # Shutdown : arrêter le scheduler
    scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scheduler_task
    logger.info("Scheduler des scans planifiés arrêté")


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
    app.include_router(scheduled_scan_router)
    app.include_router(subscription_router)
    app.include_router(preferences_router)
    app.include_router(privacy_router)
    register_exception_handlers(app)

    return app


app = create_app()
