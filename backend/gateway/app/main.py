"""Module principal de l'API Gateway.

Proxy buffer pour JSON/CSV/etc. ; proxy stream pour
tuiles vectorielles .pbf avec CORS explicite.
"""

from common.error_handlers import register_exception_handlers
from common.logging_config import get_logger, setup_logging
from common.middleware import CorrelationIdMiddleware
from common.version import get_app_version
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config_loader import settings
from .middleware import AuthMiddleware
from .routers.health import router as health_router
from .routers.proxy import register_proxy_routes

# Charger les variables d'environnement (rechargement à chaud via --reload)
load_dotenv(".env")

# --- Configuration -------------------------
config = settings()

# Configuration du logging
setup_logging(service_name="gateway")
logger = get_logger(__name__)

# --- FastAPI & Middlewares ------------------------
app = FastAPI(title=config.general.project_name, version=get_app_version())

# Middleware de correlation ID (traçabilité cross-services)
app.add_middleware(CorrelationIdMiddleware)

# Middleware d'authentification (protège toutes les routes sauf /health)
app.add_middleware(AuthMiddleware)

# Middleware CORS (doit être ajouté en dernier pour envelopper aussi les réponses d'erreur, ex: 401/403)
# Note: dans Starlette, le dernier middleware ajouté est exécuté en premier.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    allow_credentials=config.cors.allow_credentials,
)

# Routers
app.include_router(health_router)

# Enregistrement des routes de proxy
register_proxy_routes(app)

# Gestion centralisée des erreurs
register_exception_handlers(app)
