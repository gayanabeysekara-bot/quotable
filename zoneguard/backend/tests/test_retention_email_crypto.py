from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet

from app.db import session_factory
from app.models import Organisation, VideoUpload
from app.services import retention, storage

from .conftest import Api
from .helpers import create_site, create_upload_camera, synthetic_clip, upload_video


def test_retention_purges_old_video(admin: Api, tmp_path):
    cam = create_upload_camera(admin, create_site(admin)["id"])
    v = upload_video(admin, cam["id"], synthetic_clip(tmp_path)).json()
    db = session_factory()()
    try:
        row = db.get(VideoUpload, uuid.UUID(v["id"]))
        path = storage.path_for(row.storage_key)
        assert path.exists()
        org = db.get(Organisation, row.org_id)
        counts = retention.sweep_org(db, org, now=datetime.now(timezone.utc) + timedelta(days=org.video_retention_days + 1))
        db.commit()
        assert counts["videos"] == 1 and not path.exists()
    finally:
        db.close()
    assert admin.get(f"org:/videos/{v['id']}").json()["deleted_at"] is not None
    assert admin.get(f"org:/videos/{v['id']}/stream").status_code == 410


def test_retention_settings_bounded(admin: Api):
    assert admin.patch("org:", json={"video_retention_days": 0}).status_code == 422
    assert admin.patch("org:", json={"video_retention_days": 365}).status_code == 422
    r = admin.patch("org:", json={"video_retention_days": 3, "confirm_surveillance_notice": True})
    assert r.status_code == 200 and r.json()["surveillance_notice_confirmed_at"]


def test_real_smtp_delivery(monkeypatch):
    """Sends a real SMTP message to a local aiosmtpd server (the 'test email provider')."""
    from aiosmtpd.controller import Controller

    from app.config import get_settings
    from app.services.notifications import send_plain_email

    received = []

    class Handler:
        async def handle_DATA(self, server, session, envelope):
            received.append(envelope)
            return "250 OK"

    import socket

    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    ctrl = Controller(Handler(), hostname="127.0.0.1", port=port)
    ctrl.start()
    try:
        s = get_settings()
        monkeypatch.setattr(s, "email_backend", "smtp")
        monkeypatch.setattr(s, "smtp_host", "127.0.0.1")
        monkeypatch.setattr(s, "smtp_port", port)
        send_plain_email("reviewer@acme.example.com", "ZoneGuard test", "hello")
        deadline = time.time() + 5
        while not received and time.time() < deadline:
            time.sleep(0.05)
    finally:
        ctrl.stop()
    assert received and received[0].rcpt_tos == ["reviewer@acme.example.com"]
    assert b"Subject: ZoneGuard test" in received[0].content


def test_encryption_key_rotation(monkeypatch):
    from app.config import get_settings
    from app import security

    s = get_settings()
    old = s.encryption_keys
    token = security.encrypt_secret("camera-password")
    new_key = Fernet.generate_key().decode()
    monkeypatch.setattr(s, "encryption_keys", f"{new_key},{old}")
    security.reset_crypto_cache()
    try:
        assert security.decrypt_secret(token) == "camera-password"  # old ciphertext still readable
        rotated = security.rotate_secret(token)
        monkeypatch.setattr(s, "encryption_keys", new_key)  # old key retired
        security.reset_crypto_cache()
        assert security.decrypt_secret(rotated) == "camera-password"
        with pytest.raises(RuntimeError):
            security.decrypt_secret(token)
    finally:
        monkeypatch.setattr(s, "encryption_keys", old)
        security.reset_crypto_cache()


def test_cli_rotate_keys(admin: Api, monkeypatch, capsys):
    from app import cli, security
    from app.config import get_settings

    site = create_site(admin)
    cam = admin.post("org:/cameras", json={"site_id": site["id"], "name": "Gate", "source_type": "rtsp",
                                           "stream_url": "rtsp://10.0.0.9/s", "password": "pw-1"}).json()
    s = get_settings()
    old = s.encryption_keys
    new_key = Fernet.generate_key().decode()
    monkeypatch.setattr(s, "encryption_keys", f"{new_key},{old}")
    security.reset_crypto_cache()
    try:
        assert cli.main(["rotate-keys"]) == 0
        monkeypatch.setattr(s, "encryption_keys", new_key)
        security.reset_crypto_cache()
        db = session_factory()()
        from app.models import Camera

        row = db.get(Camera, uuid.UUID(cam["id"]))
        assert security.decrypt_secret(row.password_enc) == "pw-1"
        db.close()
    finally:
        monkeypatch.setattr(s, "encryption_keys", old)
        security.reset_crypto_cache()
