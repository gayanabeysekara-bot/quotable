from __future__ import annotations

from pathlib import Path

from .synthetic import make_synthetic_video


def create_site(api, name="Main Campus", tz="Australia/Sydney"):
    r = api.post("org:/sites", json={"name": name, "timezone": tz})
    assert r.status_code == 201, r.text
    return r.json()


def create_upload_camera(api, site_id, name="Admin Corridor Cam"):
    r = api.post("org:/cameras", json={"site_id": site_id, "name": name, "source_type": "upload"})
    assert r.status_code == 201, r.text
    return r.json()


def upload_video(api, camera_id, path: Path, recorded_at="2026-11-03T21:15:00+11:00", consent=True,
                 filename=None, content_type="video/mp4"):
    with open(path, "rb") as f:
        return api.post("org:/videos", data={"camera_id": camera_id, "recorded_at": recorded_at,
                                             "consent_attested": str(consent).lower()},
                        files={"file": (filename or path.name, f, content_type)})


def synthetic_clip(tmp_path) -> Path:
    return make_synthetic_video(tmp_path / "staged.mp4")
