from zoneguard_vision.detectors.base import Detection
from zoneguard_vision.geometry import point_in_polygon, segments_intersect, validate_polygon
from zoneguard_vision.tracker import IouTracker
from zoneguard_vision.video import sniff_container
from zoneguard_vision.zones import ZoneMonitor, ZoneSpec

import numpy as np
import pytest


def test_point_in_polygon():
    sq = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
    assert point_in_polygon((0.5, 0.5), sq)
    assert not point_in_polygon((0.1, 0.5), sq)


def test_segments_intersect():
    assert segments_intersect((0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1))
    assert not segments_intersect((0, 0.1), (0.4, 0.1), (0.5, 0), (0.5, 1))


def test_validate_polygon_rejects_out_of_range():
    with pytest.raises(ValueError):
        validate_polygon([(0, 0), (1.2, 0), (1, 1)])
    with pytest.raises(ValueError):
        validate_polygon([(0, 0), (1, 0)])


def _walk(x):
    return Detection("person", 0.9, (x, 0.3, x + 0.1, 0.8))


def test_tracker_keeps_anonymous_ids_and_expires():
    t = IouTracker(max_missed=2, min_hits=1)
    ids = set()
    for i in range(10):
        dets = [_walk(0.05 + i * 0.02)]
        t.update(dets)
        ids.add(dets[0].track_id)
    assert len(ids) == 1
    for _ in range(4):
        t.update([])
    assert t.tracks == []


def test_zone_entry_and_line_crossing():
    zones = [ZoneSpec("a", "Finance", "area", [(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)]),
             ZoneSpec("l", "Door", "line", [(0.3, 0.0), (0.3, 1.0)], direction="any")]
    t = IouTracker(min_hits=1)
    zm = ZoneMonitor(zones)
    events = []
    for i in range(40):
        events += zm.update(t.update([_walk(0.05 + i * 0.02)]))
    kinds = [(e.event_type, e.zone_name) for e in events]
    assert ("line_crossing", "Door") in kinds
    assert ("zone_entry", "Finance") in kinds
    assert sum(1 for k in kinds if k == ("zone_entry", "Finance")) == 1  # no duplicate while inside


def test_line_direction_filter():
    zones = [ZoneSpec("l", "Door", "line", [(0.3, 0.0), (0.3, 1.0)], direction="a_to_b")]
    t = IouTracker(min_hits=1)
    zm = ZoneMonitor(zones)
    ev = []
    for i in range(30):  # walking right-to-left
        ev += zm.update(t.update([_walk(0.8 - i * 0.02)]))
    ev_dirs = {e.attributes["direction"] for e in ev}
    assert ev_dirs <= {"a_to_b"}


def test_sniff_container():
    assert sniff_container(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 8) == "mp4"
    assert sniff_container(b"RIFF\x00\x00\x00\x00AVI LIST") == "avi"
    assert sniff_container(b"\x1a\x45\xdf\xa3" + b"\x00" * 8) == "mkv"
    assert sniff_container(b"<html><script>") is None


def test_obstruction_heuristic():
    from zoneguard_vision.obstruction import ObstructionDetector

    od = ObstructionDetector(consecutive=3)
    black = np.zeros((120, 160, 3), np.uint8)
    changes = [od.update(black) for _ in range(4)]
    assert "obstructed" in changes
    rng = np.random.default_rng(0)
    scene = rng.integers(0, 255, (120, 160, 3)).astype(np.uint8)
    assert od.update(scene) == "cleared"


def test_privacy_mask_blacks_out_region():
    from zoneguard_vision.privacy import apply_privacy_masks

    img = np.full((100, 100, 3), 200, np.uint8)
    out = apply_privacy_masks(img, [[(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)]])
    assert out[10, 10].sum() == 0 and out[90, 90].sum() > 0
    assert img[10, 10].sum() > 0  # original untouched


def test_simulated_detectors_are_labelled():
    from zoneguard_vision.detectors.face_covering import SimulatedFaceCoveringDetector
    from zoneguard_vision.detectors.weapon import SimulatedWeaponDetector

    w = SimulatedWeaponDetector(every_n=1)
    f = SimulatedFaceCoveringDetector(every_n=1)
    p = [Detection("person", 0.9, (0.1, 0.1, 0.3, 0.9), track_id=1)]
    frame = np.zeros((10, 10, 3), np.uint8)
    for d in w.detect(frame, p) + f.classify(frame, p):
        assert d.simulated and d.label.startswith("SIMULATED")
    assert w.info.status == "simulated" and f.info.status == "simulated"


def test_face_covering_classifier_rejects_demographic_labels(tmp_path):
    from zoneguard_vision.detectors.face_covering import OnnxFaceCoveringClassifier

    with pytest.raises(ValueError):
        OnnxFaceCoveringClassifier(str(tmp_path / "x.onnx"), ["balaclava", "gender_male"])
