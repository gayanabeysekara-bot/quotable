"""Geometry helpers. All coordinates are normalised to [0, 1] relative to frame size."""

from __future__ import annotations

from typing import Iterable, Sequence

Point = tuple[float, float]


def point_in_polygon(pt: Point, polygon: Sequence[Point]) -> bool:
    """Ray-casting point-in-polygon test. Points on an edge may go either way."""
    x, y = pt
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def _orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def side_of_line(pt: Point, a: Point, b: Point) -> int:
    """Return +1 / -1 for the side of directed line a->b the point is on, 0 if on it."""
    v = _orient(a, b, pt)
    if abs(v) < 1e-12:
        return 0
    return 1 if v > 0 else -1


def segments_intersect(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
    d1 = _orient(q1, q2, p1)
    d2 = _orient(q1, q2, p2)
    d3 = _orient(p1, p2, q1)
    d4 = _orient(p1, p2, q2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 != 0 and d2 != 0


def validate_polygon(points: Iterable[Sequence[float]], min_points: int = 3) -> list[Point]:
    pts = [(float(p[0]), float(p[1])) for p in points]
    if len(pts) < min_points:
        raise ValueError(f"at least {min_points} points required")
    if len(pts) > 64:
        raise ValueError("too many points (max 64)")
    for x, y in pts:
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError("coordinates must be normalised to [0, 1]")
    return pts


def bbox_anchor(bbox: Sequence[float]) -> Point:
    """Ground-contact anchor of a person box: bottom-centre (x1, y1, x2, y2)."""
    x1, _y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0
