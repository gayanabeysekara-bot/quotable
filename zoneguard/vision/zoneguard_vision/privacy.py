"""Privacy masking: blacks out configured polygons BEFORE detection, storage or display."""

from __future__ import annotations

import cv2
import numpy as np


def apply_privacy_masks(frame_bgr: np.ndarray, masks: list[list[tuple[float, float]]]) -> np.ndarray:
    if not masks:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    out = frame_bgr.copy()
    for poly in masks:
        if len(poly) < 3:
            continue
        pts = np.array([[int(x * w), int(y * h)] for x, y in poly], dtype=np.int32)
        cv2.fillPoly(out, [pts], (0, 0, 0))
    return out
