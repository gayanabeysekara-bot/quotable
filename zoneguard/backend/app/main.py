"""ZoneGuard AI API entrypoint."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import init_engine, session_factory
from .ratelimit import client_ip, limiter
from .routers import auth, cameras, edge, evaluation, incidents, orgs, videos
from .services import dispatch

log = logging.getLogger("zoneguard")

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    )


def _background_loop(stop: threading.Event) -> None:
    from .routers.edge import sweep_stale_cameras
    from .services.retention import sweep_all

    s = get_settings()
    last_retention = 0.0
    while not stop.wait(30):
        try:
            db = session_factory()()
            try:
                sweep_stale_cameras(db)
                if time.monotonic() - last_retention > s.retention_sweep_interval_s:
                    sweep_all(db)
                    last_retention = time.monotonic()
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            log.exception("background sweep failed")


def create_app() -> FastAPI:
    s = get_settings()
    s.validate_for_runtime()
    _configure_logging()
    init_engine()
    stop = threading.Event()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        dispatch.configure(workers=max(2, s.analysis_workers + 1), inline=s.environment == "test")
        t = None
        if s.run_background_tasks and s.environment != "test":
            t = threading.Thread(target=_background_loop, args=(stop,), daemon=True, name="zg-sweeper")
            t.start()
        yield
        stop.set()
        dispatch.shutdown()

    app = FastAPI(
        title="ZoneGuard AI API",
        version="0.1.0",
        description="Privacy-first AI CCTV security intelligence. Detections are observations for human review.",
        lifespan=lifespan,
        docs_url=None if s.is_production else "/api/docs",
        openapi_url=None if s.is_production else "/api/openapi.json",
    )

    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        path = request.url.path
        # Global per-IP rate limit
        if path.startswith("/api/") and not limiter.check(f"global:{client_ip(request)}", s.rate_limit_default_per_minute):
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        # CSRF defence for cookie-authenticated endpoints: SameSite=Strict cookie + a custom header that
        # cross-site forms cannot set without a CORS preflight (which this API never grants).
        if request.method in UNSAFE and path.startswith("/api/") and not path.startswith("/api/edge/"):
            if request.headers.get("x-requested-with") != "zoneguard":
                return JSONResponse({"detail": "Missing CSRF header"}, status_code=403)
        # Reject oversized non-upload bodies early
        cl = request.headers.get("content-length")
        if cl and cl.isdigit():
            limit = s.max_upload_mb * 1024 * 1024 + 1024 * 1024 if path.endswith("/videos") else 2 * 1024 * 1024
            if path.endswith("/snapshot"):
                limit = 6 * 1024 * 1024
            if int(cl) > limit:
                return JSONResponse({"detail": "Request body too large"}, status_code=413)
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if s.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        if path.startswith("/api/") and "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        log.info("request method=%s path=%s status=%s ms=%.1f rid=%s", request.method, path,
                 response.status_code, (time.perf_counter() - start) * 1000, rid)
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.exception("unhandled error on %s", request.url.path)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)

    @app.get("/api/health")
    def health():
        from sqlalchemy import text

        db = session_factory()()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "version": "0.1.0"}
        finally:
            db.close()

    for r in (auth.router, orgs.router, cameras.router, videos.router, incidents.router, edge.mgmt,
              edge.agent_api, evaluation.router):
        app.include_router(r)
    return app
