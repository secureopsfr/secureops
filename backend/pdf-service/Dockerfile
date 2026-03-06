# Image pour pdf-service (port 8013). Contexte de build attendu : backend/ (depuis la racine du repo).
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Dépendances système minimales (WeasyPrint sera ajouté lors de la migration de la logique PDF)
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
COPY pdf-service/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copier l'appli et passer en non-root
COPY --chown=appuser:appuser pdf-service/ .
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8013"]
