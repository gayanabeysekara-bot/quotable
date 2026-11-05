from __future__ import annotations

from .conftest import PASSWORD, Api, register
from .helpers import create_site, create_upload_camera


def _invite_and_join(admin: Api, client, email: str, role: str) -> Api:
    r = admin.post("org:/invitations", json={"email": email, "role": role})
    assert r.status_code == 201, r.text
    token = r.json()["invite_link"].split("token=")[1]
    user = Api(client)
    r = user.post("/api/auth/invitations/accept", json={"token": token, "full_name": role, "password": PASSWORD})
    assert r.status_code == 200, r.text
    user.org_id = admin.org_id
    return user


def test_camera_credentials_never_returned(admin: Api):
    site = create_site(admin)
    r = admin.post("org:/cameras", json={"site_id": site["id"], "name": "Gate", "source_type": "rtsp",
                                         "stream_url": "rtsp://10.0.0.5:554/stream1", "username": "viewer",
                                         "password": "s3cret-cam-pw"})
    assert r.status_code == 201
    body = r.text + admin.get("org:/cameras").text + admin.get("org:/audit").text
    assert "s3cret-cam-pw" not in body and "viewer" not in body
    assert r.json()["has_credentials"] is True


def test_credentials_in_url_rejected(admin: Api):
    site = create_site(admin)
    r = admin.post("org:/cameras", json={"site_id": site["id"], "name": "Gate", "source_type": "rtsp",
                                         "stream_url": "rtsp://admin:pw@10.0.0.5/stream"})
    assert r.status_code == 422


def test_cross_tenant_isolation(admin: Api, make_client):
    site = create_site(admin)
    cam = create_upload_camera(admin, site["id"])
    other = register(make_client(), "b@other.example.com", "Other Org")
    other_site = create_site(other, "Other HQ")
    # Org B cannot read Org A resources via its own org path either (IDs are tenant-checked)
    assert other.get(f"org:/cameras/{cam['id']}").status_code == 404
    assert other.patch(f"org:/cameras/{cam['id']}", json={"name": "pwned"}).status_code == 404
    assert other.delete(f"org:/cameras/{cam['id']}").status_code == 404
    assert other.get(f"org:/cameras/{cam['id']}/snapshot").status_code == 404
    # cannot attach zones/cameras to another tenant's objects
    assert other.post("org:/zones", json={"camera_id": cam["id"], "name": "x", "kind": "area",
                                          "points": [[0, 0], [1, 0], [1, 1]]}).status_code == 404
    assert other.post("org:/cameras", json={"site_id": site["id"], "name": "x", "source_type": "upload"}).status_code == 404
    # cannot add a foreign user as alert recipient
    me_a = admin.get("/api/auth/me").json()["id"]
    r = other.post("org:/rules", json={"name": "r", "event_type": "zone_entry", "site_id": other_site["id"],
                                       "recipient_user_ids": [me_a]})
    assert r.status_code == 422
    assert all(c["id"] != cam["id"] for c in other.get("org:/cameras").json())


def test_role_permissions_enforced_server_side(admin: Api, make_client):
    site = create_site(admin)
    auditor = _invite_and_join(admin, make_client(), "aud@acme.example.com", "auditor")
    reviewer = _invite_and_join(admin, make_client(), "rev@acme.example.com", "security_reviewer")
    manager = _invite_and_join(admin, make_client(), "sm@acme.example.com", "site_manager")
    cam_body = {"site_id": site["id"], "name": "Cam", "source_type": "upload"}
    assert auditor.post("org:/cameras", json=cam_body).status_code == 403
    assert reviewer.post("org:/cameras", json=cam_body).status_code == 403
    assert manager.post("org:/cameras", json=cam_body).status_code == 201
    assert auditor.get("org:/cameras").status_code == 200
    assert auditor.get("org:/audit").status_code == 200
    assert reviewer.get("org:/audit").status_code == 403
    assert reviewer.post("org:/rules", json={"name": "r", "event_type": "zone_entry"}).status_code == 403
    assert manager.patch("org:", json={"weapon_detection_mode": "simulated_test"}).status_code == 403
    assert manager.post("org:/invitations", json={"email": "x@acme.example.com", "role": "org_admin"}).status_code == 403
    assert admin.get("org:/me").json()["role"] == "org_admin"


def test_last_admin_cannot_be_demoted(admin: Api):
    me = admin.get("/api/auth/me").json()["id"]
    assert admin.patch(f"org:/members/{me}", json={"role": "auditor"}).status_code == 409


def test_invitation_single_use(admin: Api, make_client):
    r = admin.post("org:/invitations", json={"email": "one@acme.example.com", "role": "auditor"})
    token = r.json()["invite_link"].split("token=")[1]
    a = Api(make_client())
    assert a.post("/api/auth/invitations/accept", json={"token": token, "full_name": "x", "password": PASSWORD}).status_code == 200
    b = Api(make_client())
    assert b.post("/api/auth/invitations/accept", json={"token": token, "full_name": "x", "password": PASSWORD}).status_code == 400
