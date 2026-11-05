# Build context: zoneguard/. Runs on the customer's network (NUC / mini-PC / NVR-adjacent host).
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# opencv-python-headless wheels bundle FFmpeg, so no system packages are needed.
COPY vision /opt/vision
COPY edge_agent /opt/edge
COPY edge_agent/requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt /opt/vision /opt/edge
RUN useradd --system --uid 10001 zoneguard && mkdir -p /data && chown zoneguard /data
USER zoneguard
ENV ZG_EDGE_MODEL_DIR=/models ZG_EDGE_QUEUE_PATH=/data/edge-queue.sqlite3
VOLUME ["/data"]
ENTRYPOINT ["zoneguard-edge"]
CMD ["run"]
