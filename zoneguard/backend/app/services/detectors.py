"""Model registry for the cloud analysis worker."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from ..config import get_settings

PERSON_MODELS = {
    "yolox_nano": "Fastest, lowest accuracy. Suitable for low-power edge devices.",
    "yolox_tiny": "Default. Balanced speed / accuracy on CPU.",
    "yolox_s": "Most accurate bundled option; ~3x slower than tiny on CPU.",
}
WEAPON_MODES = ("disabled", "simulated_test", "coco_knife_unvalidated")
FACE_COVERING_MODES = ("disabled", "simulated_test")

_lock = threading.Lock()
_cache: dict[str, object] = {}

# Tests may replace this with a factory returning a clearly-labelled test double.
person_detector_factory: Callable[[str], object] | None = None


def available_person_models() -> list[dict]:
    d = Path(get_settings().model_dir)
    return [
        {"name": name, "description": desc, "available": (d / f"{name}.onnx").is_file(),
         "licence": "Apache-2.0 (YOLOX)", "task": "person"}
        for name, desc in PERSON_MODELS.items()
    ]


def get_person_detector(name: str):
    if person_detector_factory is not None:
        return person_detector_factory(name)
    if name not in PERSON_MODELS:
        raise ValueError(f"unknown person model {name}")
    with _lock:
        det = _cache.get(name)
        if det is None:
            from zoneguard_vision.detectors.yolox_onnx import YoloxOnnxDetector

            det = YoloxOnnxDetector(Path(get_settings().model_dir) / f"{name}.onnx")
            _cache[name] = det
        return det


def build_weapon(mode: str):
    from zoneguard_vision.detectors.weapon import build_weapon_detector

    return build_weapon_detector(mode, get_settings().model_dir)


def build_face_covering(mode: str):
    from zoneguard_vision.detectors.face_covering import build_face_covering_detector

    return build_face_covering_detector(mode)
