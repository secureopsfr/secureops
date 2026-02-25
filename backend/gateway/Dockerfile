FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. dépendances système pour uvicorn, sql drivers, etc.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

# 2. utilisateur non-root
RUN useradd -m appuser
WORKDIR /app

# 3. installer le package commun partagé
COPY common/ /tmp/common
RUN pip install --upgrade pip setuptools wheel \
 && pip install /tmp/common

# 4. installer les dépendances du service
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# 5. pytest cache
RUN mkdir -p .pytest_cache

# 6. copier l'app et passer en non-root
COPY --chown=appuser:appuser gateway/ .
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
