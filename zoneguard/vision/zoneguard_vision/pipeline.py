"""Per-frame processing pipeline shared by cloud analysis and the edge agent."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .detectors.base import Detection
from .detectors.face_covering import DisabledFaceCoveringDetector
from .detectors.weapon import DisabledWeaponDetector
from .obstruction import ObstructionDetector
from .privacy import apply_privacy_masks
from .tracker import IouTracker
from .zones import ZoneMonitor, ZoneSpec


@dataclass
class FrameResult:
    offset_s: float
    detections: list[dict]
    events: list[dict]
    inference_ms: float
    frame_index: int = 0


@dataclass
class PipelineConfig:
    zones: list[ZoneSpec] = field(default_factory=list)
    privacy_masks: list[list[tuple[float, float]]] = field(default_factory=list)
    weapon_event_cooldown_s: float = 10.0
    obstruction_enabled: bool = True


class FramePipeline:
    def __init__(self, person_detector, config: PipelineConfig, weapon_detector=None,
                 face_covering_detector=None, tracker: IouTracker | None = None) -> None:
        self.person_detector = person_detector
        self.config = config
        self.weapon_detector = weapon_detector or DisabledWeaponDetector()
        self.face_detector = face_covering_detector or DisabledFaceCoveringDetector()
        self.tracker = tracker or IouTracker()
        self.zone_monitor = ZoneMonitor(config.zones)
        self.obstruction = ObstructionDetector() if config.obstruction_enabled else None
        self._last_weapon_event = -1e9
        self._face_reported: set[int] = set()
        self._frame_index = 0

    def _event(self, event_type: str, offset_s: float, info, *, confidence: float | None = None,
               bbox=None, track_id=None, zone_id=None, zone_name=None, simulated=False, attributes=None) -> dict:
        return {
            "event_type": event_type,
            "offset_s": round(offset_s, 3),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "track_id": track_id,
            "confidence": None if confidence is None else round(float(confidence), 4),
            "bbox": None if bbox is None else [round(float(v), 4) for v in bbox],
            "model_name": info.name,
            "model_version": info.version,
            "model_status": info.status,
            "simulated": simulated,
            "attributes": attributes or {},
        }

    def process(self, frame_bgr: np.ndarray, offset_s: float) -> FrameResult:
        self._frame_index += 1
        events: list[dict] = []
        if self.obstruction is not None:
            change = self.obstruction.update(frame_bgr)
            if change:
                events.append({
                    "event_type": "camera_obstructed" if change == "obstructed" else "camera_obstruction_cleared",
                    "offset_s": round(offset_s, 3), "zone_id": None, "zone_name": None, "track_id": None,
                    "confidence": None, "bbox": None, "model_name": "obstruction-heuristic",
                    "model_version": "heuristic-1", "model_status": "heuristic", "simulated": False,
                    "attributes": {},
                })
        frame = apply_privacy_masks(frame_bgr, self.config.privacy_masks)
        t0 = time.perf_counter()
        persons: list[Detection] = self.person_detector.detect(frame)
        tracks = self.tracker.update(persons)
        pinfo = self.person_detector.info
        for ze in self.zone_monitor.update(tracks):
            if ze.event_type == "zone_exit":
                continue  # exits are not alert-worthy in the MVP; kept out of the event stream
            events.append(self._event(ze.event_type, offset_s, pinfo, confidence=ze.confidence, bbox=ze.bbox,
                                      track_id=ze.track_id, zone_id=ze.zone_id, zone_name=ze.zone_name,
                                      attributes=ze.attributes))
        weapons = self.weapon_detector.detect(frame, persons)
        if weapons and offset_s - self._last_weapon_event >= self.config.weapon_event_cooldown_s:
            best = max(weapons, key=lambda d: d.confidence)
            self._last_weapon_event = offset_s
            events.append(self._event("weapon_possible", offset_s, self.weapon_detector.info,
                                      confidence=best.confidence, bbox=best.bbox, simulated=best.simulated,
                                      attributes={"label": best.label}))
        coverings = self.face_detector.classify(frame, [p for p in persons if p.track_id is not None])
        for c in coverings:
            if c.track_id is not None and c.track_id in self._face_reported:
                continue
            if c.track_id is not None:
                self._face_reported.add(c.track_id)
            events.append(self._event("face_covering_observed", offset_s, self.face_detector.info,
                                      confidence=c.confidence, bbox=c.bbox, track_id=c.track_id,
                                      simulated=c.simulated, attributes={"label": c.label}))
        inference_ms = (time.perf_counter() - t0) * 1000.0
        dets = [d.as_dict() for d in persons + weapons + coverings]
        return FrameResult(offset_s, dets, events, inference_ms, self._frame_index)
