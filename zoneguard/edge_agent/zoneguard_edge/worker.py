"""Per-camera processing thread with automatic reconnect (exponential backoff + jitter)."""

from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Callable

from zoneguard_vision.pipeline import FramePipeline, PipelineConfig
from zoneguard_vision.zones import ZoneSpec

from .queue import EventQueue
from .sources import FrameSource

log = logging.getLogger("zoneguard.edge.worker")


class CameraWorker(threading.Thread):
    def __init__(self, cam: dict, source_factory: Callable[[], FrameSource], person_detector, queue: EventQueue,
                 sample_fps: float = 5.0, weapon_detector=None, face_detector=None,
                 backoff_initial: float = 1.0, backoff_max: float = 60.0, max_consecutive_failures: int = 25) -> None:
        super().__init__(daemon=True, name=f"cam-{cam['id'][:8]}")
        self.cam = cam
        self.source_factory = source_factory
        self.queue = queue
        self.sample_interval = 1.0 / max(0.1, sample_fps)
        self.pipeline = FramePipeline(
            person_detector,
            PipelineConfig(
                zones=[ZoneSpec(z["id"], z["name"], z["kind"], [tuple(p) for p in z["points"]], z.get("direction", "any"))
                       for z in cam.get("zones", [])],
                privacy_masks=[[tuple(p) for p in m] for m in cam.get("privacy_masks", [])],
            ),
            weapon_detector=weapon_detector, face_covering_detector=face_detector,
        )
        self.backoff_initial, self.backoff_max = backoff_initial, backoff_max
        self.max_consecutive_failures = max_consecutive_failures
        self._stop = threading.Event()
        self.status = "offline"
        self.last_error = ""
        self.reconnects = 0
        self.reconnect_successes = 0
        self.frames = 0
        self._fps_window: list[float] = []
        self.last_frame = None

    def stop(self) -> None:
        self._stop.set()

    @property
    def fps(self) -> float:
        w = self._fps_window
        if len(w) < 2:
            return 0.0
        return round((len(w) - 1) / max(1e-6, w[-1] - w[0]), 2)

    def health(self) -> dict:
        return {"camera_id": self.cam["id"], "status": self.status, "fps": self.fps, "reconnects": self.reconnects,
                "reconnect_successes": self.reconnect_successes, "last_error": self.last_error[:500]}

    def run(self) -> None:
        backoff = self.backoff_initial
        first = True
        while not self._stop.is_set():
            src = self.source_factory()
            if not first:
                self.reconnects += 1
            if not src.open():
                self.status, self.last_error = "offline", "unable to open stream"
                log.warning("camera %s: open failed; retry in %.1fs", self.cam["name"], backoff)
                self._stop.wait(backoff * (0.8 + 0.4 * random.random()))
                backoff = min(self.backoff_max, backoff * 2)
                first = False
                continue
            if not first:
                self.reconnect_successes += 1
            first = False
            backoff = self.backoff_initial
            self.status, self.last_error = "online", ""
            started = time.monotonic()
            failures = 0
            next_sample = 0.0
            while not self._stop.is_set():
                frame = src.read()
                if frame is None:
                    failures += 1
                    self.status = "degraded"
                    if failures >= self.max_consecutive_failures:
                        self.last_error = "stream stopped delivering frames"
                        break
                    continue
                failures = 0
                self.status = "online"
                now = time.monotonic()
                if now < next_sample:
                    continue
                next_sample = now + self.sample_interval
                self._process(frame, now - started)
            src.close()
            if not self._stop.is_set():
                self.status = "offline"
                self._stop.wait(backoff)
                backoff = min(self.backoff_max, backoff * 2)

    def _process(self, frame, offset_s: float) -> None:
        self.frames += 1
        self.last_frame = frame
        self._fps_window.append(time.monotonic())
        self._fps_window = self._fps_window[-30:]
        result = self.pipeline.process(frame, offset_s)
        now = datetime.now(timezone.utc)
        for ev in result.events:
            if ev["event_type"] == "camera_obstruction_cleared":
                continue
            self.queue.push({
                "camera_id": self.cam["id"], "zone_id": ev["zone_id"], "event_type": ev["event_type"],
                "occurred_at": (now - timedelta(milliseconds=result.inference_ms)).isoformat(),
                "track_id": ev["track_id"], "confidence": ev["confidence"], "bbox": ev["bbox"],
                "model_name": ev["model_name"], "model_version": ev["model_version"],
                "model_status": ev["model_status"], "simulated": ev["simulated"],
                "attributes": {**ev["attributes"], "detection_latency_ms": round(result.inference_ms, 1)},
            })
