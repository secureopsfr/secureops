"""Module principal de l'API Gateway.

Proxy buffer pour JSON/CSV/etc. et proxy stream pour SSE.
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

# Middleware CORS (doit être ajouté en premier pour être exécuté en dernier)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    allow_credentials=config.cors.allow_credentials,
)

# Middleware d'authentification (protège toutes les routes sauf /health)
app.add_middleware(AuthMiddleware)

# Middleware de correlation ID (traçabilité cross-services)
# Note: dernier ajouté = exécuté en premier (pile LIFO Starlette).
app.add_middleware(CorrelationIdMiddleware)

# Routers
app.include_router(health_router)

# Enregistrement des routes de proxy
register_proxy_routes(app)

# Gestion centralisée des erreurs
register_exception_handlers(app)
