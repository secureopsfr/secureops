"""Point d'entrée principal du Admin Service."""

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from common.error_handlers import register_exception_handlers
from common.logging_config import get_logger, setup_logging
from common.middleware import CorrelationIdMiddleware
from common.version import get_app_version
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from app.config_loader import settings
from app.db import init_db
from app.db_sync import init_sync_db
from app.routers.alerting import router as alerting_router
from app.routers.analytics import router as analytics_router
from app.routers.audit import router as audit_router
from app.routers.contact import router as contact_router
from app.routers.contact_public import router as contact_public_router
from app.routers.doc_pages import router as doc_pages_router
from app.routers.email_templates import router as email_templates_router
from app.routers.health import router as health_router
from app.routers.image_upload import router as image_upload_router
from app.routers.internal_notifications import router as internal_notifications_router
from app.routers.kpis import router as performance_router
from app.routers.mailing_list import router as mailing_list_router
from app.routers.newsletter import router as newsletter_router
from app.routers.notification import router as notification_router
from app.routers.subscription import router as subscription_router
from app.routers.user_management import router as user_management_router
from app.utils.auth import require_admin_user

setup_logging(service_name="admin-service")

config = settings()
logger = get_logger(__name__)

# Intervalle de rafraîchissement des vues matérialisées (en secondes)
MV_REFRESH_INTERVAL = 3600  # 1 heure

# Intervalle d'évaluation automatique des règles d'alerte (en secondes)
ALERT_CHECK_INTERVAL = 300  # 5 minutes


async def _alert_check_loop() -> None:
    """Boucle de fond qui évalue les règles d'alerte périodiquement.

    Attend un premier cycle avant de commencer (laisse le temps au service de démarrer),
    puis évalue toutes les règles actives toutes les ALERT_CHECK_INTERVAL secondes.
    """
    from app.services.alerting_service import check_alerts

    # Attendre un peu avant le premier check (laisser le temps au service de se stabiliser)
    await asyncio.sleep(60)

    while True:
        try:
            triggered = await check_alerts()
            if triggered:
                logger.info("Alertes déclenchées automatiquement : %d", len(triggered))
            else:
                logger.debug("Évaluation automatique des alertes : aucune alerte déclenchée")
        except Exception as exc:
            logger.error("Erreur lors de l'évaluation automatique des alertes: %s", exc)
        await asyncio.sleep(ALERT_CHECK_INTERVAL)


async def _mv_refresh_loop() -> None:
    """Boucle de fond qui rafraîchit les vues matérialisées toutes les heures.

    Le premier rafraîchissement est effectué immédiatement au démarrage,
    puis toutes les MV_REFRESH_INTERVAL secondes.
    """
    from app.services.materialized_views import refresh_materialized_views

    while True:
        try:
            result = await refresh_materialized_views()
            logger.info("Vues matérialisées rafraîchies : %s", result)
        except Exception as exc:
            logger.error("Erreur lors du rafraîchissement des vues matérialisées: %s", exc)
        await asyncio.sleep(MV_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: C901
    """Gère le cycle de vie de l'application (startup/shutdown).

    Args:
        app: instance de l'application FastAPI.

    Yields:
        None: permet d'exécuter le code de startup avant et shutdown après.
    """
    # Startup
    max_retries = 5
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Tentative d'initialisation de la base de données (%s/%s)", attempt, max_retries)
            await init_db()
            logger.info("Base de données asynchrone initialisée avec succès")
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

    # Initialiser la base de données synchrone pour les opérations de contenu
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Tentative d'initialisation de la base de données synchrone (%s/%s)", attempt, max_retries)
            init_sync_db()
            logger.info("Base de données synchrone initialisée avec succès")
            break
        except Exception as e:
            logger.warning("Échec de l'initialisation de la base de données synchrone: %s", e)
            if attempt < max_retries:
                logger.info("Réessai dans %s secondes...", retry_delay)
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Impossible d'initialiser la base de données synchrone après tous les essais")
                # Ne pas bloquer le démarrage si la base synchrone échoue, mais logger l'erreur
                logger.warning("L'application démarre sans la base de données synchrone. Certaines fonctionnalités ne seront pas disponibles.")

    # Lancer le scheduler de rafraîchissement des vues matérialisées (toutes les heures)
    mv_task = asyncio.create_task(_mv_refresh_loop())
    logger.info("Scheduler de rafraîchissement des vues matérialisées démarré")

    # Lancer le scheduler d'évaluation automatique des alertes (toutes les 5 minutes)
    alert_task = asyncio.create_task(_alert_check_loop())
    logger.info("Scheduler d'évaluation automatique des alertes démarré (interval: %ds)", ALERT_CHECK_INTERVAL)

    yield

    # Shutdown (nettoyage si nécessaire)
    mv_task.cancel()
    alert_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await mv_task
    with contextlib.suppress(asyncio.CancelledError):
        await alert_task
    logger.info("Arrêt de l'application")


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI."""
    app = FastAPI(title=config.general.service_name, version=get_app_version(), lifespan=lifespan)

    # Pas de CORS : ce service est interne, seul le gateway y accède.
    app.add_middleware(CorrelationIdMiddleware)

    # Routers avec leur propre préfixe complet
    app.include_router(analytics_router)
    app.include_router(health_router)
    app.include_router(performance_router)

    # Routers de contenu/admin (anciennement agrégés via content.py)
    _API = "/api"
    admin_only = [Depends(require_admin_user)]
    app.include_router(contact_router, prefix=_API, dependencies=admin_only)
    app.include_router(contact_public_router, prefix=_API)
    app.include_router(newsletter_router, prefix=_API, dependencies=admin_only)
    app.include_router(notification_router, prefix=_API, dependencies=admin_only)
    app.include_router(mailing_list_router, prefix=_API, dependencies=admin_only)
    app.include_router(image_upload_router, prefix=_API, dependencies=admin_only)
    # doc_pages : deps par route (auth pour GET, admin pour POST/PUT/DELETE)
    app.include_router(doc_pages_router, prefix=_API)
    app.include_router(email_templates_router, prefix=_API, dependencies=admin_only)
    app.include_router(user_management_router, prefix=_API, dependencies=admin_only)
    app.include_router(subscription_router, prefix=_API, dependencies=admin_only)
    app.include_router(audit_router, prefix=_API, dependencies=admin_only)
    app.include_router(alerting_router, prefix=_API, dependencies=admin_only)
    app.include_router(internal_notifications_router)

    register_exception_handlers(app)

    # Servir les fichiers statiques (images uploadées + thumbnails)
    images_dir = os.path.join(os.path.dirname(__file__), "..", "data", "images", "uploads")
    thumbs_dir = os.path.join(images_dir, "thumbnails")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(thumbs_dir, exist_ok=True)
    # Le sous-dossier thumbnails doit être monté en premier (plus spécifique)
    app.mount("/images/uploads/thumbnails", StaticFiles(directory=thumbs_dir), name="thumbnails")
    app.mount("/images/uploads", StaticFiles(directory=images_dir), name="uploaded-images")

    return app


app = create_app()
