"""Visible-weapon detection module — EXPERIMENTAL.

No adequately trained, commercially licensed, validated weapon-detection model is bundled
with ZoneGuard AI. This module therefore provides:

* ``disabled``               – default. Produces nothing.
* ``simulated_test``         – deterministic SIMULATED detections for exercising the alert
                               workflow end-to-end. Every output has ``simulated=True`` and a
                               label prefixed with ``SIMULATED``. Never use in production.
* ``coco_knife_unvalidated`` – the generic COCO "knife" class from YOLOX. COCO knives are mostly
                               kitchen/table knives. This is NOT a weapon detector, has no firearm
                               class, and has not been validated. Outputs are labelled
                               "possible knife (unvalidated generic class)".
* ``onnx_custom``            – loads a customer-supplied, appropriately licensed YOLOX-format ONNX
                               model with its own class list. Validation is the supplier's /
                               customer's responsibility and must be documented before use.

All outputs are *possible objects*, never confirmed threats. Nothing in this module (or the
alert engine) triggers emergency calls, lockdowns or other high-impact automatic actions.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .base import Detection, DetectorInfo


class DisabledWeaponDetector:
    info = DetectorInfo("weapon-disabled", "n/a", "weapon", "disabled", "n/a")

    def detect(self, frame_bgr: np.ndarray, persons: list[Detection] | None = None) -> list[Detection]:
        return []


class SimulatedWeaponDetector:
    """Emits a simulated 'possible knife' next to the first person every ``every_n`` frames."""

    info = DetectorInfo(
        "weapon-simulated", "sim-1", "weapon", "simulated", "n/a",
        notes="SIMULATED test mode. Outputs are not predictions of any model.",
    )

    def __init__(self, every_n: int = 15) -> None:
        self.every_n = max(1, every_n)
        self._n = 0

    def detect(self, frame_bgr: np.ndarray, persons: list[Detection] | None = None) -> list[Detection]:
        self._n += 1
        if not persons or self._n % self.every_n:
            return []
        x1, y1, x2, y2 = persons[0].bbox
        w = x2 - x1
        box = (min(1.0, x2 - w * 0.2), (y1 + y2) / 2, min(1.0, x2 + w * 0.2), min(1.0, (y1 + y2) / 2 + w * 0.3))
        return [
            Detection(
                label="SIMULATED possible knife",
                confidence=0.5,
                bbox=box,
                category="weapon",
                simulated=True,
            )
        ]


class OnnxObjectWeaponDetector:
    """Wraps a YOLOX-format ONNX model for experimental prohibited-object detection."""

    def __init__(self, model_path: str, classes: tuple[str, ...], info: DetectorInfo,
                 conf_threshold: float = 0.4, class_names: tuple[str, ...] | None = None) -> None:
        from . import yolox_onnx

        self.info = info
        names = class_names or yolox_onnx.COCO_CLASSES
        self._det = yolox_onnx.YoloxOnnxDetector(
            model_path, conf_threshold=conf_threshold, classes=classes,
            verify_checksum=class_names is None, class_names=names,
        )
        self._names = names

    def detect(self, frame_bgr: np.ndarray, persons: list[Detection] | None = None) -> list[Detection]:
        out = []
        for cid, score, bbox in self._det.raw_detect(frame_bgr):
            out.append(
                Detection(
                    label=f"possible {self._names[cid]}" + (
                        " (unvalidated generic class)" if self.info.name == "coco-knife-unvalidated" else ""
                    ),
                    confidence=score,
                    bbox=bbox,
                    category="weapon",
                )
            )
        return out


def build_weapon_detector(mode: str, model_dir: str | Path, *, custom_model: str | None = None,
                          custom_classes: tuple[str, ...] = (), custom_class_names: tuple[str, ...] = (),
                          conf_threshold: float = 0.4):
    mode = (mode or "disabled").lower()
    if mode == "disabled":
        return DisabledWeaponDetector()
    if mode == "simulated_test":
        return SimulatedWeaponDetector()
    if mode == "coco_knife_unvalidated":
        info = DetectorInfo(
            "coco-knife-unvalidated", "yolox_tiny@0.1.1rc0", "weapon", "experimental", "Apache-2.0 (YOLOX)",
            notes="Generic COCO 'knife' class. Not a validated weapon detector. No firearm class.",
        )
        return OnnxObjectWeaponDetector(str(Path(model_dir) / "yolox_tiny.onnx"), ("knife",), info, conf_threshold)
    if mode == "onnx_custom":
        if not custom_model or not custom_classes or not custom_class_names:
            raise ValueError("onnx_custom weapon mode needs model path, classes and class names")
        info = DetectorInfo(
            f"custom-weapon:{Path(custom_model).stem}", "customer-supplied", "weapon", "experimental",
            "customer-supplied — licence must be reviewed",
        )
        return OnnxObjectWeaponDetector(custom_model, custom_classes, info, conf_threshold, custom_class_names)
    raise ValueError(f"unknown weapon detector mode: {mode}")
