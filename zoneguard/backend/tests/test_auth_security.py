from __future__ import annotations

import pyotp

from .conftest import PASSWORD, Api, register


def test_register_rejects_weak_password(client):
    api = Api(client)
    r = api.post("/api/auth/register", json={"email": "a@acme.example.com", "password": "alllowercase123",
                                             "full_name": "A", "organisation_name": "Org"})
    assert r.status_code == 422


def test_session_cookie_flags(client):
    api = Api(client)
    r = api.post("/api/auth/register", json={"email": "c@acme.example.com", "password": PASSWORD,
                                             "full_name": "C", "organisation_name": "Org"})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie


def test_csrf_header_required(admin: Api):
    r = admin.c.post(f"/api/orgs/{admin.org_id}/sites", json={"name": "x"})
    assert r.status_code == 403
    assert admin.post("org:/sites", json={"name": "x"}).status_code == 201


def test_login_failure_and_lockout(client):
    register(client, "lock@acme.example.com")
    api = Api(client)
    api.post("/api/auth/logout")
    for _ in range(8):
        assert api.post("/api/auth/login", json={"email": "lock@acme.example.com", "password": "Wrong-pass-123"}).status_code == 401
    # locked: even the right password fails for now
    assert api.post("/api/auth/login", json={"email": "lock@acme.example.com", "password": PASSWORD}).status_code == 401
    assert api.post("/api/auth/login", json={"email": "nobody@acme.example.com", "password": PASSWORD}).status_code == 401


def test_logout_revokes_session(admin: Api):
    cookie = admin.c.cookies.get("zg_session")
    admin.post("/api/auth/logout")
    admin.c.cookies.set("zg_session", cookie)
    assert admin.get("/api/auth/me").status_code == 401


def test_mfa_totp_flow(admin: Api):
    setup = admin.post("/api/auth/mfa/setup").json()
    totp = pyotp.TOTP(setup["secret"])
    assert admin.post("/api/auth/mfa/enable", json={"code": "000000"}).status_code == 400
    assert admin.post("/api/auth/mfa/enable", json={"code": totp.now()}).status_code == 200
    admin.post("/api/auth/logout")
    r = admin.post("/api/auth/login", json={"email": "admin@acme.example.com", "password": PASSWORD})
    assert r.json()["mfa_required"] is True
    assert admin.get("/api/auth/me").status_code == 401  # half-authenticated session is not enough
    assert admin.get("org:/sites").status_code == 401
    assert admin.post("/api/auth/mfa/verify", json={"code": totp.now()}).status_code == 200
    assert admin.get("/api/auth/me").json()["mfa_enabled"] is True


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_password_change_revokes_other_sessions(admin: Api, make_client):
    other = Api(make_client())
    other.post("/api/auth/login", json={"email": "admin@acme.example.com", "password": PASSWORD})
    assert other.get("/api/auth/me").status_code == 200
    assert admin.post("/api/auth/password", json={"current_password": PASSWORD,
                                                  "new_password": "Another-Strong-99"}).status_code == 200
    assert other.get("/api/auth/me").status_code == 401
    assert admin.get("/api/auth/me").status_code == 200
