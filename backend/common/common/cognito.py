"""Configuration Cognito centralisée pour tous les micro-services.

Charge les variables d'environnement Cognito une seule fois et expose
les constantes ``REGION``, ``USERPOOL_ID``, ``CLIENT_ID``, ``JWKS_URL``
et ``ISSUER`` utilisées par le vérificateur JWT et les services admin.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

# Idempotent — ne surcharge pas les vars déjà définies (Docker, export…).
load_dotenv(override=False)

logger = logging.getLogger(__name__)

# ── Variables d'environnement Cognito ────────────────────────────────────

REGION: str = os.getenv("COGNITO_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-3"))
USERPOOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")

# ── URL dérivées ─────────────────────────────────────────────────────────

_jwks_env = os.getenv("COGNITO_JWKS_URL")
if _jwks_env:
    JWKS_URL: str = _jwks_env
elif REGION and USERPOOL_ID:
    JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USERPOOL_ID}/.well-known/jwks.json"
else:
    JWKS_URL = ""

ISSUER: str = os.getenv(
    "COGNITO_ISSUER_URL",
    f"https://cognito-idp.{REGION}.amazonaws.com/{USERPOOL_ID}" if REGION and USERPOOL_ID else "",
)

# ── Log de démarrage ─────────────────────────────────────────────────────

logger.info("=== Configuration Cognito (common) ===")
logger.info("REGION: %s", REGION)
logger.info("USERPOOL_ID: %s", "✓ défini" if USERPOOL_ID else "✗ manquant")
logger.info("CLIENT_ID: %s", "✓ défini" if CLIENT_ID else "✗ manquant")
logger.info("JWKS_URL: %s", JWKS_URL or "non disponible")
logger.info("ISSUER: %s", ISSUER or "non disponible")
logger.info("======================================")
