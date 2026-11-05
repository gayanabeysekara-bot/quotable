"""Short-lived anonymous object tracker (IoU association, no appearance features).

Track IDs are integers local to one camera view and one processing session. They are not
linked across cameras, are not persisted as identities, and expire after ``max_missed`` frames.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .detectors.base import Detection
from .geometry import iou


@dataclass
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    hits: int = 1
    missed: int = 0
    history: list[tuple[float, float]] = field(default_factory=list)  # recent anchors only


class IouTracker:
    def __init__(self, iou_threshold: float = 0.25, max_missed: int = 8, min_hits: int = 2,
                 history_len: int = 30) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self.min_hits = min_hits
        self.history_len = history_len
        self.tracks: list[Track] = []
        self._next_id = 1

    def update(self, detections: list[Detection]) -> list[Track]:
        """Associate detections to tracks greedily by IoU. Sets ``track_id`` on detections.

        Returns confirmed tracks (``hits >= min_hits``) that were matched this frame.
        """
        from .geometry import bbox_anchor

        pairs = []
        for ti, t in enumerate(self.tracks):
            for di, d in enumerate(detections):
                v = iou(t.bbox, d.bbox)
                if v >= self.iou_threshold:
                    pairs.append((v, ti, di))
        pairs.sort(reverse=True)
        used_t, used_d = set(), set()
        for _v, ti, di in pairs:
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            t = self.tracks[ti]
            d = detections[di]
            t.bbox, t.confidence = d.bbox, d.confidence
            t.hits += 1
            t.missed = 0
            d.track_id = t.track_id
        for ti, t in enumerate(self.tracks):
            if ti not in used_t:
                t.missed += 1
        for di, d in enumerate(detections):
            if di not in used_d:
                t = Track(self._next_id, d.bbox, d.confidence)
                self._next_id += 1
                self.tracks.append(t)
                used_t.add(len(self.tracks) - 1)
                d.track_id = t.track_id
        self.tracks = [t for t in self.tracks if t.missed <= self.max_missed]
        active = []
        for t in self.tracks:
            if t.missed == 0:
                t.history.append(bbox_anchor(t.bbox))
                if len(t.history) > self.history_len:
                    t.history.pop(0)
                if t.hits >= self.min_hits:
                    active.append(t)
        return active

    def reset(self) -> None:
        self.tracks.clear()
