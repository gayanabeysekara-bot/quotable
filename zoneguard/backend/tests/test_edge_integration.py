"""Edge agent <-> cloud API integration: real agent code talking to the real API (in-process)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from zoneguard_edge.agent import EdgeAgent
from zoneguard_edge.client import CloudClient
from zoneguard_edge.config import EdgeConfig

from app.services.notifications import memory_outbox

from .conftest import Api
from .helpers import create_site
from .synthetic import BlobTestDetector, make_synthetic_video


def _setup(admin: Api, tmp_path, stream_url="rtsp://10.1.1.9:554/live"):
    site = create_site(admin)
    r = admin.post("org:/edge-agents", json={"site_id": site["id"], "name": "Office NUC"})
    assert r.status_code == 201
    token = r.json()["token"]
    agent_id = r.json()["agent"]["id"]
    cam = admin.post("org:/cameras", json={"site_id": site["id"], "name": "Finance door", "source_type": "rtsp",
                                           "stream_url": stream_url, "username": "viewer", "password": "cam-pw-1",
                                           "edge_agent_id": agent_id}).json()
    return site, cam, token


def _edge_client(admin: Api, token: str, tmp_path) -> CloudClient:
    cfg = EdgeConfig(api_url="http://testserver", token=token, queue_path=tmp_path / "q.sqlite3",
                     allow_insecure_http=True)
    client = CloudClient(cfg)
    client._http = admin.c.__class__(admin.c.app, base_url="http://testserver",
                                     headers={"Authorization": f"Bearer {token}"})
    return client


def test_edge_config_delivers_credentials_only_to_agent(admin: Api, tmp_path):
    _site, cam, token = _setup(admin, tmp_path)
    client = _edge_client(admin, token, tmp_path)
    conf = client.get_config()
    assert conf["cameras"][0]["password"] == "cam-pw-1"
    assert "cam-pw-1" not in admin.get(f"org:/cameras/{cam['id']}").text
    bad = admin.c.get("/api/edge/config", headers={"Authorization": "Bearer zge_not-a-real-token"})
    assert bad.status_code == 401


def test_edge_events_idempotent_and_scoped(admin: Api, tmp_path, make_client):
    site, cam, token = _setup(admin, tmp_path)
    admin.post("org:/rules", json={"name": "Door any time", "event_type": "line_crossing", "camera_id": cam["id"]})
    client = _edge_client(admin, token, tmp_path)
    ev = {"idempotency_key": "evt-00000001", "camera_id": cam["id"], "event_type": "line_crossing",
          "occurred_at": datetime.now(timezone.utc).isoformat(), "confidence": 0.8, "model_name": "yolox_tiny"}
    assert client.post_events([ev])["accepted"] == 1
    assert client.post_events([ev])["duplicates"] == 1  # retry after outage is safe
    assert len(admin.get("org:/incidents").json()) == 1
    # camera from another tenant is rejected
    from .conftest import register

    other = register(make_client(), "edge-other@other.example.com", "Other")
    osite = create_site(other)
    ocam = other.post("org:/cameras", json={"site_id": osite["id"], "name": "x", "source_type": "upload"}).json()
    res = client.post_events([{**ev, "idempotency_key": "evt-00000002", "camera_id": ocam["id"]}])
    assert res["rejected"] == 1 and other.get("org:/events").json() == []
    # future timestamps rejected
    fut = {**ev, "idempotency_key": "evt-00000003", "occurred_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()}
    assert client.post_events([fut])["rejected"] == 1


def test_heartbeat_offline_raises_camera_offline_incident(admin: Api, tmp_path):
    _site, cam, token = _setup(admin, tmp_path)
    admin.post("org:/rules", json={"name": "Camera down", "event_type": "camera_offline", "severity": "review_required"})
    client = _edge_client(admin, token, tmp_path)
    client.heartbeat({"version": "0.1.0", "cameras": [{"camera_id": cam["id"], "status": "online", "fps": 5}]})
    assert admin.get(f"org:/cameras/{cam['id']}").json()["status"] == "online"
    client.heartbeat({"version": "0.1.0", "cameras": [{"camera_id": cam["id"], "status": "offline",
                                                        "reconnects": 3, "reconnect_successes": 2,
                                                        "last_error": "unable to open stream"}]})
    assert admin.get(f"org:/cameras/{cam['id']}").json()["status"] == "offline"
    incs = admin.get("org:/incidents").json()
    assert len(incs) == 1 and incs[0]["category"] == "camera_offline"
    assert len(memory_outbox.messages) == 1
    m = admin.get("org:/metrics").json()
    assert m["camera_reconnects"]["success_rate"] == round(2 / 3, 3)


def test_revoked_agent_rejected(admin: Api, tmp_path):
    _site, _cam, token = _setup(admin, tmp_path)
    agent_id = admin.get("org:/edge-agents").json()[0]["id"]
    admin.delete(f"org:/edge-agents/{agent_id}")
    r = admin.c.get("/api/edge/config", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_agent_processes_local_stream_and_syncs_metadata(admin: Api, tmp_path):
    """Full edge path: local file stream -> worker -> local queue -> sync -> cloud rule -> incident."""
    clip = make_synthetic_video(tmp_path / "door.mp4", seconds=4, fps=10)
    site, cam, token = _setup(admin, tmp_path, stream_url="rtsp://10.1.1.9/live")
    admin.patch(f"org:/cameras/{cam['id']}", json={"stream_url": "rtsp://10.1.1.9/live"})
    zone = admin.post("org:/zones", json={"camera_id": cam["id"], "name": "Staff entrance", "kind": "line",
                                          "points": [[0.5, 0.0], [0.5, 1.0]]}).json()
    admin.post("org:/rules", json={"name": "Entrance crossing", "event_type": "line_crossing", "zone_id": zone["id"]})
    client = _edge_client(admin, token, tmp_path)
    cfg = EdgeConfig(api_url="http://testserver", token=token, queue_path=tmp_path / "edge.sqlite3",
                     allow_insecure_http=True, sample_fps=20)
    agent = EdgeAgent(cfg, client=client, detector_factory=BlobTestDetector)
    conf = agent.load_config()
    # The test points the configured camera at a local file instead of real RTSP hardware.
    conf["cameras"][0]["stream_url"] = f"file://{clip}"
    import zoneguard_edge.agent as agent_mod
    from zoneguard_edge.sources import OpenCvSource

    orig = agent_mod.source_for_camera
    agent_mod.source_for_camera = lambda c: OpenCvSource(c["stream_url"][7:], loop_file=False)
    try:
        agent.apply_config(conf)
        deadline = time.time() + 15
        while time.time() < deadline and agent.queue.depth() == 0:
            time.sleep(0.1)
        agent.stop()
    finally:
        agent_mod.source_for_camera = orig
    assert agent.queue.depth() >= 1
    assert agent.sync_once() >= 1 and agent.queue.depth() == 0
    events = admin.get("org:/events?event_type=line_crossing").json()
    assert events and events[0]["source"] == "edge" and events[0]["zone_id"] == zone["id"]
    assert "detection_latency_ms" in events[0]["attributes"]
    incs = admin.get("org:/incidents").json()
    assert len(incs) == 1 and incs[0]["rule_name"] == "Entrance crossing"
    assert not (tmp_path / "edge.config.json").read_text().count("cam-pw-1")  # secrets never cached to disk
