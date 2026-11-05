"""Genuine AI person detection with the bundled YOLOX ONNX models.

Requires model files (scripts/download_models.sh) and a sample clip containing people. By default
this uses OpenCV's public sample ``vtest.avi`` (pedestrians); set ZG_SAMPLE_VIDEO to use your own
staged, consented footage. Tests are skipped — not faked — when assets are missing.

These tests check that the real model runs and finds people; they do NOT measure accuracy.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from .conftest import Api
from .helpers import create_site, create_upload_camera, upload_video

MODELS = Path(os.environ["ZG_MODEL_DIR"])
SAMPLE = Path(os.environ.get("ZG_SAMPLE_VIDEO", Path(__file__).resolve().parents[2] / "samples" / "vtest.avi"))

needs_assets = pytest.mark.skipif(not (MODELS / "yolox_tiny.onnx").exists() or not SAMPLE.exists(),
                                  reason="model or sample video not downloaded (see README)")


@needs_assets
def test_yolox_detects_people_in_sample():
    from zoneguard_vision.detectors.yolox_onnx import YoloxOnnxDetector
    from zoneguard_vision.video import iter_sampled_frames

    det = YoloxOnnxDetector(MODELS / "yolox_tiny.onnx")
    counts = [len(det.detect(f)) for _t, _i, f in iter_sampled_frames(SAMPLE, 2, max_frames=10)]
    assert sum(counts) > 0
    assert det.info.licence.startswith("Apache-2.0")


@needs_assets
def test_real_model_analysis_via_api(admin: Api):
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    r = upload_video(admin, cam["id"], SAMPLE, recorded_at="2026-11-03T22:00:00+11:00", content_type="video/x-msvideo")
    assert r.status_code == 201, r.text
    video = r.json()
    admin.post("org:/zones", json={"camera_id": cam["id"], "name": "Lower walkway", "kind": "area",
                                   "points": [[0.0, 0.6], [1.0, 0.6], [1.0, 1.0], [0.0, 1.0]]})
    admin.post("org:/rules", json={"name": "Walkway after hours", "event_type": "zone_entry",
                                   "schedule": [{"days": [0, 1, 2, 3, 4, 5, 6], "start": "18:00", "end": "06:00"}],
                                   "suppression_seconds": 30})
    job = admin.post(f"org:/videos/{video['id']}/analyses", json={"model_name": "yolox_nano", "sample_fps": 2}).json()
    job = admin.get(f"org:/analyses/{job['id']}").json()
    assert job["status"] == "completed", job["error"]
    assert job["model_version"] == "yolox_nano@0.1.1rc0"
    assert job["stats"]["max_persons_in_frame"] >= 1
    frames = admin.get(f"org:/analyses/{job['id']}/detections").json()["frames"]
    persons = [d for f in frames for d in f["detections"] if d["category"] == "person"]
    assert persons and all(0 <= d["confidence"] <= 1 for d in persons)
    events = admin.get(f"org:/analyses/{job['id']}/events").json()
    assert any(e["event_type"] == "zone_entry" for e in events)
    assert admin.get("org:/incidents").json()  # real detections drove a potential incident
    r = admin.get(f"org:/videos/{video['id']}/frame?t=3&job_id={job['id']}")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
