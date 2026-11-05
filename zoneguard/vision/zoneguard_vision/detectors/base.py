from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class DetectorInfo:
    """Provenance attached to every detection so reviewers know exactly what produced it."""

    name: str
    version: str
    task: str  # person | weapon | face_covering
    status: str  # production-candidate | experimental | simulated | disabled
    licence: str
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # normalised x1, y1, x2, y2
    category: str = "person"  # person | weapon | face_covering
    simulated: bool = False
    track_id: int | None = None
    attributes: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = {
            "label": self.label,
            "confidence": round(float(self.confidence), 4),
            "bbox": [round(float(v), 4) for v in self.bbox],
            "category": self.category,
            "simulated": self.simulated,
        }
        if self.track_id is not None:
            d["track_id"] = self.track_id
        if self.attributes:
            d["attributes"] = self.attributes
        return d


class Detector(Protocol):
    info: DetectorInfo

    def detect(self, frame_bgr: np.ndarray) -> list[Detection]: ...
