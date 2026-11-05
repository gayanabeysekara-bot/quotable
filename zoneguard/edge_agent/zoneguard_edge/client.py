from __future__ import annotations

import httpx

from . import __version__
from .config import EdgeConfig


class CloudError(RuntimeError):
    pass


class CloudClient:
    def __init__(self, cfg: EdgeConfig, transport: httpx.BaseTransport | None = None) -> None:
        verify = cfg.ca_bundle or True
        self._http = httpx.Client(
            base_url=cfg.api_url, timeout=15.0, verify=verify, transport=transport,
            headers={"Authorization": f"Bearer {cfg.token}", "User-Agent": f"zoneguard-edge/{__version__}"},
        )

    def _req(self, method: str, path: str, **kw):
        try:
            r = self._http.request(method, path, **kw)
        except httpx.HTTPError as exc:
            raise CloudError(f"network error: {exc}") from exc
        if r.status_code == 401:
            raise CloudError("edge token rejected (revoked or invalid)")
        if r.status_code >= 400:
            raise CloudError(f"HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    def get_config(self) -> dict:
        return self._req("GET", "/api/edge/config")

    def heartbeat(self, body: dict) -> dict:
        return self._req("POST", "/api/edge/heartbeat", json=body)

    def post_events(self, events: list[dict]) -> dict:
        return self._req("POST", "/api/edge/events", json={"events": events})

    def post_discovery(self, devices: list[dict]) -> dict:
        return self._req("POST", "/api/edge/discovery", json=devices)

    def post_snapshot(self, camera_id: str, jpeg: bytes) -> dict:
        return self._req("POST", f"/api/edge/cameras/{camera_id}/snapshot",
                         files={"file": ("snapshot.jpg", jpeg, "image/jpeg")})

    def close(self) -> None:
        self._http.close()
