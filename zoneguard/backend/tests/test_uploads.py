from __future__ import annotations

import io

from .conftest import Api
from .helpers import create_site, create_upload_camera, synthetic_clip, upload_video


def _cam(admin):
    return create_upload_camera(admin, create_site(admin)["id"])


def test_rejects_non_video_content(admin: Api):
    cam = _cam(admin)
    r = admin.post("org:/videos", data={"camera_id": cam["id"], "recorded_at": "2026-11-03T21:00:00+11:00",
                                        "consent_attested": "true"},
                   files={"file": ("evil.mp4", io.BytesIO(b"<script>alert(1)</script>" * 10), "video/mp4")})
    assert r.status_code == 415


def test_rejects_disallowed_extension(admin: Api, tmp_path):
    cam = _cam(admin)
    assert upload_video(admin, cam["id"], synthetic_clip(tmp_path), filename="clip.exe").status_code == 415


def test_rejects_extension_mismatch(admin: Api, tmp_path):
    cam = _cam(admin)
    r = upload_video(admin, cam["id"], synthetic_clip(tmp_path), filename="clip.avi")
    assert r.status_code == 422


def test_requires_consent_attestation(admin: Api, tmp_path):
    cam = _cam(admin)
    assert upload_video(admin, cam["id"], synthetic_clip(tmp_path), consent=False).status_code == 422


def test_requires_timezone_on_recorded_at(admin: Api, tmp_path):
    cam = _cam(admin)
    r = upload_video(admin, cam["id"], synthetic_clip(tmp_path), recorded_at="2026-11-03T21:00:00")
    assert r.status_code == 422


def test_rejects_truncated_container(admin: Api, tmp_path):
    cam = _cam(admin)
    data = synthetic_clip(tmp_path).read_bytes()[:64]  # valid magic, undecodable body
    p = tmp_path / "trunc.mp4"
    p.write_bytes(data)
    assert upload_video(admin, cam["id"], p).status_code == 422


def test_size_limit(admin: Api, tmp_path, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    cam = _cam(admin)
    assert upload_video(admin, cam["id"], synthetic_clip(tmp_path)).status_code == 413


def test_delete_video_removes_file_and_blocks_stream(admin: Api, tmp_path):
    cam = _cam(admin)
    v = upload_video(admin, cam["id"], synthetic_clip(tmp_path)).json()
    assert admin.get(f"org:/videos/{v['id']}/stream").status_code == 200
    assert admin.delete(f"org:/videos/{v['id']}").status_code == 200
    assert admin.get(f"org:/videos/{v['id']}/stream").status_code == 410


def test_snapshot_and_annotated_frame(admin: Api, tmp_path):
    cam = _cam(admin)
    upload_video(admin, cam["id"], synthetic_clip(tmp_path))
    r = admin.get(f"org:/cameras/{cam['id']}/snapshot")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
