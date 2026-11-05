"""Detector evaluation metrics. Pure functions — no I/O — so they are easy to test and audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass

Box = tuple[float, float, float, float]


def iou(a: Box, b: Box) -> float:
    ix1, iy1, ix2, iy2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


@dataclass
class DetectionCounts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p and r else None

    def as_dict(self) -> dict:
        return {**asdict(self), "precision": self.precision, "recall": self.recall, "f1": self.f1}


def match_frame(preds: list[tuple[Box, float]], gts: list[Box], iou_threshold: float = 0.5) -> DetectionCounts:
    """Greedy matching by confidence (standard PASCAL-style). Each GT matches at most one prediction."""
    c = DetectionCounts()
    used: set[int] = set()
    for box, _conf in sorted(preds, key=lambda x: -x[1]):
        best, best_i = 0.0, -1
        for i, g in enumerate(gts):
            if i in used:
                continue
            v = iou(box, g)
            if v > best:
                best, best_i = v, i
        if best >= iou_threshold:
            used.add(best_i)
            c.tp += 1
        else:
            c.fp += 1
    c.fn += len(gts) - len(used)
    return c


def accumulate(frames: list[tuple[list[tuple[Box, float]], list[Box]]], iou_threshold: float = 0.5) -> DetectionCounts:
    total = DetectionCounts()
    for preds, gts in frames:
        c = match_frame(preds, gts, iou_threshold)
        total.tp += c.tp
        total.fp += c.fp
        total.fn += c.fn
    return total


def match_events(predicted_t: list[float], truth_t: list[float], tolerance_s: float = 2.0) -> DetectionCounts:
    """Event-level matching (e.g. zone entries) with a time tolerance."""
    c = DetectionCounts()
    used: set[int] = set()
    for t in sorted(predicted_t):
        best_i, best_d = -1, tolerance_s + 1
        for i, g in enumerate(truth_t):
            if i not in used and abs(g - t) <= tolerance_s and abs(g - t) < best_d:
                best_i, best_d = i, abs(g - t)
        if best_i >= 0:
            used.add(best_i)
            c.tp += 1
        else:
            c.fp += 1
    c.fn = len(truth_t) - len(used)
    return c


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def false_alerts_per_camera_per_day(false_alerts: int, cameras: int, hours_observed: float) -> float | None:
    if cameras <= 0 or hours_observed <= 0:
        return None
    return false_alerts / cameras / (hours_observed / 24.0)
