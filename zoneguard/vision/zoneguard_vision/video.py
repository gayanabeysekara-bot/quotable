"""Safe video probing and frame iteration for uploaded staged footage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

ALLOWED_EXTENSIONS = {".mp4": "mp4", ".m4v": "mp4", ".mov": "mov", ".avi": "avi", ".mkv": "mkv", ".webm": "webm"}


class VideoValidationError(ValueError):
    pass


def sniff_container(head: bytes) -> str | None:
    """Identify the container from magic bytes (never trust the extension or Content-Type)."""
    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        return "mov" if brand == b"qt  " else "mp4"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "mkv"  # Matroska / WebM share the EBML header
    return None


@dataclass
class VideoInfo:
    container: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration_s: float


def probe_video(path: str | Path, *, max_duration_s: float = 1800, max_pixels: int = 3840 * 2160) -> VideoInfo:
    p = Path(path)
    with open(p, "rb") as f:
        head = f.read(32)
    container = sniff_container(head)
    ext = ALLOWED_EXTENSIONS.get(p.suffix.lower())
    if container is None or ext is None:
        raise VideoValidationError("unsupported or unrecognised video container")
    if not (container == ext or {container, ext} <= {"mp4", "mov"} or {container, ext} <= {"mkv", "webm"}):
        raise VideoValidationError("file extension does not match file contents")
    cap = cv2.VideoCapture(str(p))
    try:
        if not cap.isOpened():
            raise VideoValidationError("video could not be decoded")
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise VideoValidationError("video contains no decodable frames")
    finally:
        cap.release()
    if w <= 0 or h <= 0 or w * h > max_pixels:
        raise VideoValidationError("unsupported resolution")
    if fps <= 0 or fps > 240:
        fps = 25.0
    duration = n / fps if n > 0 else 0.0
    if duration > max_duration_s:
        raise VideoValidationError(f"video longer than the {int(max_duration_s)}s limit")
    return VideoInfo(container, w, h, fps, n, duration)


def iter_sampled_frames(path: str | Path, sample_fps: float = 5.0,
                        max_frames: int | None = None) -> Iterator[tuple[float, int, np.ndarray]]:
    """Yield (offset_seconds, source_frame_index, frame) at approximately ``sample_fps``."""
    cap = cv2.VideoCapture(str(path))
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0) or 25.0
        step = max(1, round(fps / max(sample_fps, 0.1)))
        idx = 0
        emitted = 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            if idx % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                yield idx / fps, idx, frame
                emitted += 1
                if max_frames and emitted >= max_frames:
                    break
            idx += 1
    finally:
        cap.release()


def read_frame_at(path: str | Path, offset_s: float) -> np.ndarray | None:
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, offset_s) * 1000.0)
        ok, frame = cap.read()
        return frame if ok else None
    finally:
        cap.release()
