"""Heuristic camera obstruction / tamper check (NOT an ML model).

Flags frames that are almost uniformly dark, washed out, or featureless (e.g. lens covered,
camera spray-painted, pointed at a wall). Requires several consecutive frames to fire.
Threshold tuning per camera is expected; false positives are possible in very dark scenes.
"""

from __future__ import annotations

import cv2
import numpy as np


class ObstructionDetector:
    def __init__(self, dark_mean: float = 18.0, bright_mean: float = 240.0, min_std: float = 8.0,
                 min_edge_ratio: float = 0.002, consecutive: int = 10) -> None:
        self.dark_mean, self.bright_mean, self.min_std = dark_mean, bright_mean, min_std
        self.min_edge_ratio = min_edge_ratio
        self.consecutive = consecutive
        self._count = 0
        self.active = False

    @staticmethod
    def frame_stats(frame_bgr: np.ndarray) -> dict:
        gray = cv2.cvtColor(cv2.resize(frame_bgr, (160, 120)), cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return {"mean": float(gray.mean()), "std": float(gray.std()), "edge_ratio": float((edges > 0).mean())}

    def update(self, frame_bgr: np.ndarray) -> str | None:
        """Return 'obstructed' / 'cleared' on state change, else None."""
        s = self.frame_stats(frame_bgr)
        suspicious = (
            s["mean"] < self.dark_mean
            or s["mean"] > self.bright_mean
            or (s["std"] < self.min_std and s["edge_ratio"] < self.min_edge_ratio)
        )
        self._count = self._count + 1 if suspicious else 0
        if not self.active and self._count >= self.consecutive:
            self.active = True
            return "obstructed"
        if self.active and self._count == 0:
            self.active = False
            return "cleared"
        return None
