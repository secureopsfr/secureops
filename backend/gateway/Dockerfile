FROM python:3.11-slim
ARG INSTALL_DEV_DEPS=false

# 1. utilisateur non-root
RUN useradd -m appuser
WORKDIR /app

# 2. installer le package commun partagé
COPY common/ /tmp/common
RUN pip install --upgrade pip setuptools wheel \
 && pip install /tmp/common

# 3. installer les dépendances du service
COPY gateway/requirements.txt gateway/requirements-dev.txt ./
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
 && if [ "$INSTALL_DEV_DEPS" = "true" ] && [ -f requirements-dev.txt ]; then \
      pip install --no-cache-dir --prefer-binary -r requirements-dev.txt; \
    fi

# 4. pytest cache
RUN mkdir -p .pytest_cache

# 5. copier l'app et passer en non-root
COPY --chown=appuser:appuser gateway/ .
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
