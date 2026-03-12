# Image pour scan-service (port 8012). Contexte de build attendu : backend/ (depuis la racine du repo).
FROM python:3.11-slim
ARG INSTALL_DEV_DEPS=false

ENV DEBIAN_FRONTEND=noninteractive

# Dépendances système
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
RUN useradd -m appuser
WORKDIR /app

# Installer le package commun partagé
COPY common/ /tmp/common
RUN pip install --upgrade pip setuptools wheel \
 && pip install /tmp/common

# Installer dépendances du service
COPY scan-service/requirements.txt scan-service/requirements-dev.txt ./
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
 && if [ "$INSTALL_DEV_DEPS" = "true" ] && [ -f requirements-dev.txt ]; then \
      pip install --no-cache-dir --prefer-binary -r requirements-dev.txt; \
    fi

# Copier l'appli et passer en non-root
COPY --chown=appuser:appuser scan-service/ .
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]
