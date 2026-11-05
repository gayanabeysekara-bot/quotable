"""Edge agent orchestration: config sync, camera workers, metadata sync, heartbeats."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path

import psutil

from . import __version__
from .client import CloudClient, CloudError
from .config import EdgeConfig
from .queue import EventQueue
from .sources import source_for_camera
from .worker import CameraWorker

log = logging.getLogger("zoneguard.edge")


class EdgeAgent:
    def __init__(self, cfg: EdgeConfig, client: CloudClient | None = None, detector_factory=None) -> None:
        self.cfg = cfg
        self.client = client or CloudClient(cfg)
        self.queue = EventQueue(cfg.queue_path, cfg.max_queue_events)
        self.workers: dict[str, CameraWorker] = {}
        self._config_sig = ""
        self._stop = threading.Event()
        self._detector_factory = detector_factory or self._default_detector
        self._detector = None
        self.cache_path = Path(cfg.queue_path).with_suffix(".config.json")
        self.sync_failures = 0

    def _default_detector(self):
        from zoneguard_vision.detectors.yolox_onnx import YoloxOnnxDetector

        return YoloxOnnxDetector(self.cfg.model_dir / f"{self.cfg.person_model}.onnx")

    # ---------- config ----------
    def load_config(self) -> dict | None:
        try:
            conf = self.client.get_config()
            # Cache WITHOUT credentials so the agent can keep processing during an outage restart only if
            # credentials are supplied locally; secrets are never written to disk.
            safe = {**conf, "cameras": [{k: v for k, v in c.items() if k not in ("username", "password")}
                                        for c in conf["cameras"]]}
            self.cache_path.write_text(json.dumps(safe))
            os.chmod(self.cache_path, 0o600)
            return conf
        except CloudError as exc:
            log.warning("config fetch failed: %s", exc)
            if self.cache_path.exists() and not self.workers:
                log.warning("using cached config (cameras requiring credentials cannot start until the cloud is reachable)")
                return json.loads(self.cache_path.read_text())
            return None

    def apply_config(self, conf: dict) -> None:
        sig = json.dumps(conf["cameras"], sort_keys=True) + json.dumps(conf.get("features", {}), sort_keys=True)
        if sig == self._config_sig:
            return
        self._config_sig = sig
        for w in self.workers.values():
            w.stop()
        self.workers.clear()
        if self._detector is None:
            self._detector = self._detector_factory()
        from zoneguard_vision.detectors.face_covering import build_face_covering_detector
        from zoneguard_vision.detectors.weapon import build_weapon_detector

        feats = conf.get("features", {})
        for cam in conf["cameras"]:
            try:
                source_for_camera(cam)  # validate early
            except ValueError as exc:
                log.warning("skipping camera %s: %s", cam.get("name"), exc)
                continue
            w = CameraWorker(
                cam, lambda c=cam: source_for_camera(c), self._detector, self.queue, self.cfg.sample_fps,
                weapon_detector=build_weapon_detector(feats.get("weapon_detection_mode", "disabled"), self.cfg.model_dir),
                face_detector=build_face_covering_detector(feats.get("face_covering_mode", "disabled")),
            )
            self.workers[cam["id"]] = w
            w.start()
        log.info("started %d camera workers", len(self.workers))

    # ---------- sync ----------
    def sync_once(self, batch: int = 200) -> int:
        items = self.queue.peek(batch)
        if not items:
            return 0
        seqs = [s for s, _ in items]
        try:
            res = self.client.post_events([e for _, e in items])
        except CloudError as exc:
            self.queue.mark_attempt(seqs)
            self.sync_failures += 1
            log.warning("event sync failed (%d queued): %s", self.queue.depth(), exc)
            return -1
        # accepted, duplicates and permanently rejected events are all removed from the queue
        self.queue.ack(seqs)
        self.sync_failures = 0
        if res.get("rejected"):
            log.warning("cloud rejected %s events (camera/zone no longer valid)", res["rejected"])
        return len(seqs)

    def heartbeat(self) -> None:
        p = psutil.Process()
        self.client.heartbeat({
            "version": __version__, "queue_depth": self.queue.depth(), "cpu_percent": psutil.cpu_percent(None),
            "rss_mb": round(p.memory_info().rss / 1e6, 1), "cameras": [w.health() for w in self.workers.values()],
        })

    def run(self) -> None:
        last_hb = last_conf = 0.0
        backoff = 1.0
        while not self._stop.is_set():
            now = time.monotonic()
            if now - last_conf > self.cfg.config_refresh_s or not self._config_sig:
                conf = self.load_config()
                if conf:
                    self.apply_config(conf)
                last_conf = now
            if now - last_hb > self.cfg.heartbeat_interval_s:
                try:
                    self.heartbeat()
                except CloudError as exc:
                    log.warning("heartbeat failed: %s", exc)
                last_hb = now
            n = self.sync_once()
            if n < 0:
                self._stop.wait(backoff)
                backoff = min(60.0, backoff * 2)
            else:
                backoff = 1.0
                self._stop.wait(0.5 if n else 2.0)

    def stop(self) -> None:
        self._stop.set()
        for w in self.workers.values():
            w.stop()
