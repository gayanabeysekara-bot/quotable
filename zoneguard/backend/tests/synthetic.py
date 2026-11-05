"""Synthetic test fixtures.

* ``make_synthetic_video`` renders a deterministic clip: textured grey background with a bright
  upright rectangle moving left -> right. It contains NO people and is NOT used to claim model
  accuracy — it exercises upload validation, zone geometry and the event/incident pipeline.
* ``BlobTestDetector`` is a clearly labelled TEST DOUBLE (classical thresholding, not ML) that
  finds the rectangle. Real-model tests live in test_real_detection.py.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from zoneguard_vision.detectors.base import Detection, DetectorInfo


def make_synthetic_video(path: str | Path, seconds: float = 6.0, fps: int = 10, size=(320, 240),
                         fourcc: str = "mp4v") -> Path:
    path = Path(path)
    w, h = size
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*fourcc), fps, (w, h))
    rng = np.random.default_rng(42)
    bg = (rng.integers(90, 140, size=(h, w, 3))).astype(np.uint8)
    n = int(seconds * fps)
    for i in range(n):
        frame = bg.copy()
        x = int(10 + (w - 50) * i / max(1, n - 1))
        cv2.rectangle(frame, (x, 80), (x + 30, 200), (255, 255, 255), -1)
        vw.write(frame)
    vw.release()
    return path


class BlobTestDetector:
    info = DetectorInfo("blob-test-double", "test-1", "person", "test-double", "n/a",
                        notes="TEST DOUBLE: thresholding, not a model. Used only in automated tests.")

    def detect(self, frame_bgr: np.ndarray) -> list[Detection]:
        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = []
        for c in contours:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw * bh < 200:
                continue
            out.append(Detection("person (test double)", 0.9, (x / w, y / h, (x + bw) / w, (y + bh) / h)))
        return out
