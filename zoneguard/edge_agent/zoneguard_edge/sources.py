"""Camera source abstraction. Add new integrations by implementing ``FrameSource``."""

from __future__ import annotations

import os
import time
from typing import Protocol
from urllib.parse import quote, urlsplit, urlunsplit

import numpy as np


class FrameSource(Protocol):
    def open(self) -> bool: ...
    def read(self) -> np.ndarray | None: ...
    def close(self) -> None: ...


def inject_credentials(url: str, username: str | None, password: str | None) -> str:
    """Build the URL OpenCV/FFmpeg needs. The result is held in memory only and never logged."""
    if not username:
        return url
    p = urlsplit(url)
    auth = quote(username, safe="") + (":" + quote(password or "", safe="") if password is not None else "")
    host = p.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    netloc = f"{auth}@{host}" + (f":{p.port}" if p.port else "")
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))


def redact(url: str) -> str:
    p = urlsplit(url)
    if p.username or p.password:
        host = p.hostname + (f":{p.port}" if p.port else "")
        return urlunsplit((p.scheme, f"***@{host}", p.path, p.query, p.fragment))
    return url


class OpenCvSource:
    """RTSP/HTTP stream (or local file) via OpenCV's FFmpeg backend. Read-only: frames are only pulled."""

    def __init__(self, url: str, username: str | None = None, password: str | None = None,
                 loop_file: bool = False, transport: str = "tcp", timeout_ms: int = 10000) -> None:
        self._url = inject_credentials(url, username, password)
        self.display_url = redact(self._url)
        self.loop_file = loop_file
        self._cap = None
        self._transport = transport
        self._timeout_ms = timeout_ms
        self._file_fps = 0.0
        self._last_read = 0.0

    def open(self) -> bool:
        import cv2

        if self._url.startswith("rtsp"):
            os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS",
                                  f"rtsp_transport;{self._transport}|stimeout;{self._timeout_ms * 1000}")
        self.close()
        cap = cv2.VideoCapture(self._url, cv2.CAP_FFMPEG)
        try:
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self._timeout_ms)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self._timeout_ms)
        except Exception:  # noqa: BLE001 - older OpenCV builds
            pass
        if not cap.isOpened():
            cap.release()
            return False
        self._cap = cap
        if "://" not in self._url:  # local file used for demos: pace at native fps
            self._file_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        return True

    def read(self) -> np.ndarray | None:
        import cv2

        if self._cap is None:
            return None
        if self._file_fps:
            delay = 1.0 / self._file_fps - (time.monotonic() - self._last_read)
            if delay > 0:
                time.sleep(delay)
            self._last_read = time.monotonic()
        ok, frame = self._cap.read()
        if not ok and self.loop_file and self._file_fps:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


def source_for_camera(cam: dict) -> FrameSource:
    url = cam.get("stream_url") or ""
    if url.startswith("file://"):
        return OpenCvSource(url[len("file://"):], loop_file=True)
    if not url:
        raise ValueError(f"camera {cam.get('name')} has no stream URL (ONVIF media URL resolution is a TODO)")
    return OpenCvSource(url, cam.get("username"), cam.get("password"))
