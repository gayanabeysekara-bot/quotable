# Build context: zoneguard/ (see docker-compose.yml)
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# opencv-python-headless wheels bundle FFmpeg, so no system packages are needed.
WORKDIR /app
COPY vision /opt/vision
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt /opt/vision
COPY backend/ /app/
RUN useradd --system --uid 10001 zoneguard && mkdir -p /data/uploads && chown -R zoneguard /data
USER zoneguard
ENV ZG_STORAGE_DIR=/data/uploads ZG_MODEL_DIR=/models
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.asgi:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
