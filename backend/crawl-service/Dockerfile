# Image pour crawl-service (port 8014). Contexte de build attendu : backend/
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
WORKDIR /app

COPY common/ /tmp/common
RUN pip install --upgrade pip setuptools wheel \
 && pip install /tmp/common

COPY crawl-service/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright
RUN playwright install --with-deps chromium

COPY --chown=appuser:appuser crawl-service/ .
RUN chown -R appuser:appuser /app/ms-playwright 2>/dev/null || true
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8014"]
