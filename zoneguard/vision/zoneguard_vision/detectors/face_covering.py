"""Optional face-covering observation module.

Strict scope (enforced by design, see docs/SECURITY_PRIVACY.md):
* No facial recognition, no face embeddings, no identity matching, no persistent face profiles.
* No inference of ethnicity, religion, gender, age or any other demographic attribute.
* Output is a neutral *observation* about a visible covering on an anonymous person box.
  The alert engine caps face-covering rules at "informational" and never escalates on it alone.

Modes:
* ``disabled``        – default.
* ``simulated_test``  – SIMULATED observations for workflow testing (``simulated=True``).
* ``onnx_classifier`` – customer-supplied, licensed image classifier applied to the upper region
                        of each person box. Labels are supplied with the model. No model is bundled.
"""

from __future__ import annotations

import numpy as np

from .base import Detection, DetectorInfo

ALLOWED_LABELS = {"no_covering", "medical_mask", "full_face_covering", "balaclava", "unknown"}


class DisabledFaceCoveringDetector:
    info = DetectorInfo("face-covering-disabled", "n/a", "face_covering", "disabled", "n/a")

    def classify(self, frame_bgr: np.ndarray, persons: list[Detection]) -> list[Detection]:
        return []


class SimulatedFaceCoveringDetector:
    info = DetectorInfo(
        "face-covering-simulated", "sim-1", "face_covering", "simulated", "n/a",
        notes="SIMULATED test mode. Outputs are not predictions of any model.",
    )

    def __init__(self, every_n: int = 15) -> None:
        self.every_n = max(1, every_n)
        self._n = 0

    def classify(self, frame_bgr: np.ndarray, persons: list[Detection]) -> list[Detection]:
        self._n += 1
        if not persons or self._n % self.every_n:
            return []
        p = persons[0]
        x1, y1, x2, y2 = p.bbox
        return [Detection("SIMULATED medical_mask", 0.5, (x1, y1, x2, y1 + (y2 - y1) * 0.25),
                          category="face_covering", simulated=True, track_id=p.track_id)]


class OnnxFaceCoveringClassifier:
    def __init__(self, model_path: str, labels: list[str], input_size: int = 224,
                 conf_threshold: float = 0.6) -> None:
        import onnxruntime as ort

        bad = set(labels) - ALLOWED_LABELS
        if bad:
            raise ValueError(f"labels not permitted for this module: {sorted(bad)}")
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.labels = labels
        self.input_size = input_size
        self.conf_threshold = conf_threshold
        self.info = DetectorInfo("face-covering-custom", "customer-supplied", "face_covering",
                                 "experimental", "customer-supplied — licence must be reviewed")

    def classify(self, frame_bgr: np.ndarray, persons: list[Detection]) -> list[Detection]:
        import cv2

        h, w = frame_bgr.shape[:2]
        out = []
        for p in persons:
            x1, y1, x2, y2 = p.bbox
            hy2 = y1 + (y2 - y1) * 0.3  # upper body / head region of the anonymous box
            crop = frame_bgr[int(y1 * h): int(hy2 * h), int(x1 * w): int(x2 * w)]
            if crop.size == 0 or crop.shape[0] < 12 or crop.shape[1] < 12:
                continue
            img = cv2.resize(crop, (self.input_size, self.input_size))[:, :, ::-1].astype(np.float32) / 255.0
            logits = self.session.run(None, {self.input_name: img.transpose(2, 0, 1)[None]})[0][0]
            e = np.exp(logits - logits.max())
            probs = e / e.sum()
            i = int(probs.argmax())
            if self.labels[i] in ("no_covering", "unknown") or probs[i] < self.conf_threshold:
                continue
            out.append(Detection(self.labels[i], float(probs[i]), (x1, y1, x2, hy2),
                                 category="face_covering", track_id=p.track_id))
        return out


def build_face_covering_detector(mode: str, *, model_path: str | None = None, labels: list[str] | None = None):
    mode = (mode or "disabled").lower()
    if mode == "disabled":
        return DisabledFaceCoveringDetector()
    if mode == "simulated_test":
        return SimulatedFaceCoveringDetector()
    if mode == "onnx_classifier":
        if not model_path or not labels:
            raise ValueError("onnx_classifier needs model_path and labels")
        return OnnxFaceCoveringClassifier(model_path, labels)
    raise ValueError(f"unknown face covering mode: {mode}")
