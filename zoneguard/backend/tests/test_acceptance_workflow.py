"""End-to-end acceptance workflow (brief §14), driven through the HTTP API.

Person detection here uses a clearly-labelled TEST DOUBLE so the zone/rule/incident path is
deterministic; genuine YOLOX detection is exercised in test_real_detection.py.
"""

from __future__ import annotations

from app.services import detectors
from app.services.notifications import memory_outbox

from .conftest import PASSWORD, Api, register
from .helpers import create_site, create_upload_camera, synthetic_clip, upload_video
from .synthetic import BlobTestDetector


def test_full_acceptance_workflow(admin: Api, make_client, tmp_path):
    detectors.person_detector_factory = lambda name: BlobTestDetector()
    # 1. authorised user logs in (register created a session; log out and back in explicitly)
    assert admin.post("/api/auth/logout").status_code == 200
    assert admin.get("/api/auth/me").status_code == 401
    r = admin.post("/api/auth/login", json={"email": "admin@acme.example.com", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["mfa_required"] is False
    # 2. create a site
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    # 3. add staged CCTV video (recorded 9:15 PM Sydney time = after hours)
    r = upload_video(admin, cam["id"], synthetic_clip(tmp_path))
    assert r.status_code == 201, r.text
    video = r.json()
    assert video["duration_s"] > 5 and video["container"] == "mp4"
    # 5. define restricted monitoring zone (right half of the frame) with approved access 08:00-17:00
    r = admin.post("org:/zones", json={
        "camera_id": cam["id"], "name": "Finance Office", "kind": "area",
        "points": [[0.55, 0.0], [1.0, 0.0], [1.0, 1.0], [0.55, 1.0]],
        "approved_access": [{"days": [0, 1, 2, 3, 4], "start": "08:00", "end": "17:00"}],
    })
    assert r.status_code == 201, r.text
    zone = r.json()
    # 7. after-hours rule: Finance Office between 6 PM and 6 AM -> alert the site manager (admin here)
    r = admin.post("org:/rules", json={
        "name": "Finance after hours", "event_type": "zone_entry", "zone_id": zone["id"], "camera_id": cam["id"],
        "schedule": [{"days": [0, 1, 2, 3, 4, 5, 6], "start": "18:00", "end": "06:00"}],
        "severity": "high_priority", "min_confidence": 0.5, "suppression_seconds": 300,
    })
    assert r.status_code == 201, r.text
    # 4 & 6. run analysis; person crosses into the zone
    r = admin.post(f"org:/videos/{video['id']}/analyses", json={"model_name": "yolox_tiny", "sample_fps": 5})
    assert r.status_code == 202, r.text
    job = admin.get(f"org:/analyses/{r.json()['id']}").json()
    assert job["status"] == "completed", job
    assert job["stats"]["frames_processed"] > 20
    events = admin.get(f"org:/analyses/{job['id']}/events").json()
    entries = [e for e in events if e["event_type"] == "zone_entry"]
    assert len(entries) == 1 and entries[0]["zone_id"] == zone["id"]
    dets = admin.get(f"org:/analyses/{job['id']}/detections").json()["frames"]
    assert any(f["detections"] for f in dets) and "bbox" in dets[5]["detections"][0]
    # 8. incident appears
    incs = admin.get("org:/incidents?status=active").json()
    assert len(incs) == 1, [(e["rule_outcome"], e["occurred_at"]) for e in entries]
    inc = incs[0]
    assert inc["severity"] == "high_priority" and inc["zone_name"] == "Finance Office"
    assert inc["model_version"] == "test-1" and inc["rule_name"] == "Finance after hours"
    assert "unauthori" not in inc["title"].lower()
    # 9. email notification delivered via the configured (in-memory test) provider, without imagery
    assert len(memory_outbox.messages) == 1
    msg = memory_outbox.messages[0]
    assert msg.to == "admin@acme.example.com" and inc["reference"] in msg.subject
    assert "No images are attached" in msg.body and "bbox" not in msg.body
    detail = admin.get(f"org:/incidents/{inc['id']}").json()
    assert detail["notifications"][0]["status"] == "sent"
    # 10. review actions
    assert admin.post(f"org:/incidents/{inc['id']}/actions", json={"action": "acknowledge"}).status_code == 200
    assert admin.post(f"org:/incidents/{inc['id']}/notes", json={"note": "Checked roster."}).status_code == 201
    assert admin.post(f"org:/incidents/{inc['id']}/actions", json={"action": "escalate", "note": "Call SM"}).status_code == 200
    r = admin.post(f"org:/incidents/{inc['id']}/actions", json={"action": "close", "reason": "resolved"})
    assert r.status_code == 200 and r.json()["status"] == "closed"
    # invalid transition rejected
    assert admin.post(f"org:/incidents/{inc['id']}/actions", json={"action": "escalate"}).status_code == 409
    # 11. complete history recorded
    hist = admin.get(f"org:/incidents/{inc['id']}").json()["history"]
    assert [h["action"] for h in hist] == ["created", "acknowledge", "note_added", "escalate", "close"]
    audit_actions = {a["action"] for a in admin.get("org:/audit").json()}
    assert {"incident.acknowledge", "incident.escalate", "incident.close", "video.uploaded",
            "zone.created", "rule.created"} <= audit_actions
    # 12. unauthorised user cannot access the organisation's information
    outsider = register(make_client(), "intruder@other.example.com", "Other Org")
    for path in ("", "/sites", "/cameras", "/incidents", f"/incidents/{inc['id']}", "/audit",
                 f"/videos/{video['id']}/stream"):
        r = outsider.c.get(f"/api/orgs/{admin.org_id}{path}")
        assert r.status_code == 404, (path, r.status_code)
    r = outsider.post(f"/api/orgs/{admin.org_id}/incidents/{inc['id']}/actions", json={"action": "reopen"})
    assert r.status_code == 404
    anon = make_client()
    assert anon.get(f"/api/orgs/{admin.org_id}/incidents").status_code == 401


def test_approved_access_period_creates_no_incident(admin: Api, tmp_path):
    detectors.person_detector_factory = lambda name: BlobTestDetector()
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    video = upload_video(admin, cam["id"], synthetic_clip(tmp_path), recorded_at="2026-11-03T10:00:00+11:00").json()
    zone = admin.post("org:/zones", json={
        "camera_id": cam["id"], "name": "Records Room", "kind": "area",
        "points": [[0.55, 0.0], [1.0, 0.0], [1.0, 1.0], [0.55, 1.0]],
        "approved_access": [{"days": [0, 1, 2, 3, 4], "start": "08:00", "end": "17:00"}]}).json()
    admin.post("org:/rules", json={"name": "Any entry", "event_type": "zone_entry", "zone_id": zone["id"]})
    job = admin.post(f"org:/videos/{video['id']}/analyses", json={"model_name": "yolox_tiny"}).json()
    events = admin.get(f"org:/analyses/{job['id']}/events").json()
    assert events and events[0]["rule_outcome"] == "within_approved_access_period"
    assert admin.get("org:/incidents").json() == []


def test_suppression_folds_repeat_events(admin: Api, tmp_path):
    detectors.person_detector_factory = lambda name: BlobTestDetector()
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    video = upload_video(admin, cam["id"], synthetic_clip(tmp_path)).json()
    admin.post("org:/zones", json={"camera_id": cam["id"], "name": "Staff door", "kind": "line",
                                   "points": [[0.5, 0.0], [0.5, 1.0]]})
    admin.post("org:/rules", json={"name": "Crossings", "event_type": "line_crossing", "camera_id": cam["id"],
                                   "suppression_seconds": 600})
    # The same footage analysed twice yields repeat events at the same times: folded into one incident.
    for _ in range(2):
        job = admin.post(f"org:/videos/{video['id']}/analyses", json={"model_name": "yolox_tiny"}).json()
        events = admin.get(f"org:/analyses/{job['id']}/events").json()
        assert len([e for e in events if e["event_type"] == "line_crossing"]) == 1
    incs = admin.get("org:/incidents").json()
    assert len(incs) == 1 and incs[0]["suppressed_count"] == 1
    assert "suppressed_into" in events[0]["rule_outcome"]


def test_specialist_detectors_gated_by_org_flags(admin: Api, tmp_path):
    detectors.person_detector_factory = lambda name: BlobTestDetector()
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    video = upload_video(admin, cam["id"], synthetic_clip(tmp_path)).json()
    r = admin.post(f"org:/videos/{video['id']}/analyses", json={"model_name": "yolox_tiny", "weapon_mode": "simulated_test"})
    assert r.status_code == 403
    admin.patch("org:", json={"weapon_detection_mode": "simulated_test", "face_covering_mode": "simulated_test"})
    admin.post("org:/rules", json={"name": "Weapon", "event_type": "weapon_possible", "severity": "critical_review"})
    admin.post("org:/rules", json={"name": "Covering", "event_type": "face_covering_observed",
                                   "severity": "critical_review"})
    job = admin.post(f"org:/videos/{video['id']}/analyses", json={
        "model_name": "yolox_tiny", "weapon_mode": "simulated_test", "face_covering_mode": "simulated_test"}).json()
    incs = admin.get("org:/incidents").json()
    weapon = [i for i in incs if i["category"] == "weapon_possible"]
    cover = [i for i in incs if i["category"] == "face_covering_observed"]
    assert weapon and all(i["simulated"] and i["title"].startswith("SIMULATED") for i in weapon)
    assert cover and all(i["severity"] == "informational" for i in cover)  # neutral observation, capped
    rules = admin.get("org:/rules").json()
    assert next(r for r in rules if r["event_type"] == "face_covering_observed")["severity"] == "informational"
