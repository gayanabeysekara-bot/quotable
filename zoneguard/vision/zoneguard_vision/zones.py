"""Zone monitoring: restricted-area entry and entrance-boundary (line) crossing."""

from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import point_in_polygon, side_of_line
from .tracker import Track


@dataclass
class ZoneSpec:
    zone_id: str
    name: str
    kind: str  # "area" (polygon) | "line" (entrance boundary, 2 points)
    points: list[tuple[float, float]]
    direction: str = "any"  # line only: any | a_to_b (left->right of directed line) | b_to_a


@dataclass
class ZoneEvent:
    event_type: str  # zone_entry | zone_exit | line_crossing
    zone_id: str
    zone_name: str
    track_id: int
    confidence: float
    bbox: tuple[float, float, float, float]
    attributes: dict = field(default_factory=dict)


class ZoneMonitor:
    def __init__(self, zones: list[ZoneSpec]) -> None:
        self.zones = zones
        self._inside: dict[tuple[str, int], bool] = {}
        self._side: dict[tuple[str, int], tuple[int, tuple[float, float]]] = {}
        self._last_seen: dict[int, int] = {}
        self._tick = 0
        self.forget_after = 50  # updates; covers short occlusions without keeping state forever

    @staticmethod
    def _within_extent(p0, p1, a, b) -> bool:
        """True if the crossing between p0 and p1 happens within the boundary segment a-b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy or 1e-12
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        t = ((mid[0] - a[0]) * dx + (mid[1] - a[1]) * dy) / length2
        return -0.02 <= t <= 1.02

    def update(self, tracks: list[Track]) -> list[ZoneEvent]:
        events: list[ZoneEvent] = []
        self._tick += 1
        for t in tracks:
            self._last_seen[t.track_id] = self._tick
        for t in tracks:
            if not t.history:
                continue
            anchor = t.history[-1]
            for z in self.zones:
                if z.kind == "area":
                    key = (z.zone_id, t.track_id)
                    now_in = point_in_polygon(anchor, z.points)
                    was_in = self._inside.get(key)
                    if now_in and not was_in:
                        events.append(ZoneEvent("zone_entry", z.zone_id, z.name, t.track_id, t.confidence, t.bbox,
                                                {"first_seen_inside": was_in is None}))
                    elif was_in and not now_in:
                        events.append(ZoneEvent("zone_exit", z.zone_id, z.name, t.track_id, t.confidence, t.bbox))
                    self._inside[key] = now_in
                elif z.kind == "line" and len(z.points) == 2:
                    a, b = z.points
                    key = (z.zone_id, t.track_id)
                    s_now = side_of_line(anchor, a, b)
                    if s_now == 0:
                        continue  # exactly on the line: wait until the track is clearly on one side
                    last = self._side.get(key)
                    self._side[key] = (s_now, anchor)
                    if last is not None and last[0] != s_now and self._within_extent(last[1], anchor, a, b):
                        direction = "a_to_b" if last[0] > 0 else "b_to_a"
                        if z.direction in ("any", direction):
                            events.append(ZoneEvent("line_crossing", z.zone_id, z.name, t.track_id, t.confidence,
                                                    t.bbox, {"direction": direction}))
        # forget state of tracks no longer present so memory stays bounded
        stale = {tid for tid, seen in self._last_seen.items() if self._tick - seen > self.forget_after}
        if stale:
            self._inside = {k: v for k, v in self._inside.items() if k[1] not in stale}
            self._side = {k: v for k, v in self._side.items() if k[1] not in stale}
            for tid in stale:
                self._last_seen.pop(tid, None)
        return events
