from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


@dataclass
class EdgeConfig:
    api_url: str
    token: str = field(repr=False)
    model_dir: Path = Path("/models")
    person_model: str = "yolox_tiny"
    queue_path: Path = Path("/data/edge-queue.sqlite3")
    sample_fps: float = 5.0
    ca_bundle: str | None = None
    allow_insecure_http: bool = False
    heartbeat_interval_s: float = 30.0
    config_refresh_s: float = 300.0
    max_queue_events: int = 100_000

    @classmethod
    def from_env(cls) -> "EdgeConfig":
        def b(name: str) -> bool:
            return os.environ.get(name, "").lower() in ("1", "true", "yes")

        api = os.environ.get("ZG_EDGE_API_URL", "").rstrip("/")
        token = os.environ.get("ZG_EDGE_TOKEN", "")
        if not api or not token:
            raise SystemExit("ZG_EDGE_API_URL and ZG_EDGE_TOKEN must be set")
        cfg = cls(
            api_url=api,
            token=token,
            model_dir=Path(os.environ.get("ZG_EDGE_MODEL_DIR", "/models")),
            person_model=os.environ.get("ZG_EDGE_PERSON_MODEL", "yolox_tiny"),
            queue_path=Path(os.environ.get("ZG_EDGE_QUEUE_PATH", "/data/edge-queue.sqlite3")),
            sample_fps=float(os.environ.get("ZG_EDGE_SAMPLE_FPS", "5")),
            ca_bundle=os.environ.get("ZG_EDGE_CA_BUNDLE") or None,
            allow_insecure_http=b("ZG_EDGE_ALLOW_INSECURE_HTTP"),
        )
        cfg.validate()
        return cfg

    def validate(self) -> None:
        parts = urlsplit(self.api_url)
        local = parts.hostname in ("localhost", "127.0.0.1", "::1", "api", "backend")
        if parts.scheme != "https" and not (local and self.allow_insecure_http):
            raise SystemExit(
                "Refusing to send data over plain HTTP. Use https://, or for local development only set "
                "ZG_EDGE_ALLOW_INSECURE_HTTP=true with a localhost API URL."
            )
