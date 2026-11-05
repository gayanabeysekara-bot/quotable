from __future__ import annotations

import time

import numpy as np
import pytest

from zoneguard_edge.agent import EdgeAgent
from zoneguard_edge.client import CloudError
from zoneguard_edge.config import EdgeConfig
from zoneguard_edge.discovery import parse_probe_match
from zoneguard_edge.queue import EventQueue
from zoneguard_edge.sources import inject_credentials, redact
from zoneguard_edge.worker import CameraWorker
from zoneguard_vision.detectors.base import Detection, DetectorInfo


def test_queue_survives_restart(tmp_path):
    q = EventQueue(tmp_path / "q.sqlite3")
    q.push({"event_type": "zone_entry", "idempotency_key": "k1"})
    q.push({"event_type": "zone_entry", "idempotency_key": "k1"})  # duplicate key ignored
    q.push({"event_type": "line_crossing"})
    q.close()
    q2 = EventQueue(tmp_path / "q.sqlite3")
    assert q2.depth() == 2
    items = q2.peek()
    q2.ack([items[0][0]])
    assert q2.depth() == 1


def test_queue_is_bounded(tmp_path):
    q = EventQueue(tmp_path / "q.sqlite3", max_events=5)
    for i in range(8):
        q.push({"n": i})
    assert q.depth() == 5 and q.dropped == 3
    assert q.peek()[0][1]["n"] == 3  # oldest dropped first


def test_credentials_injected_and_redacted():
    url = inject_credentials("rtsp://10.0.0.5:554/Streaming/101", "view@er", "p:ss/w")
    assert url == "rtsp://view%40er:p%3Ass%2Fw@10.0.0.5:554/Streaming/101"
    assert "p%3Ass" not in redact(url) and redact(url).startswith("rtsp://***@10.0.0.5:554")


def test_refuses_plain_http_to_remote():
    with pytest.raises(SystemExit):
        EdgeConfig(api_url="http://zoneguard.example.com", token="zge_x").validate()
    EdgeConfig(api_url="http://localhost:8000", token="zge_x", allow_insecure_http=True).validate()
    EdgeConfig(api_url="https://zoneguard.example.com", token="zge_x").validate()


def test_parse_probe_match():
    xml = b"""<?xml version="1.0"?><s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
    xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
    <s:Body><d:ProbeMatches><d:ProbeMatch><a:EndpointReference><a:Address>urn:uuid:1234</a:Address></a:EndpointReference>
    <d:Scopes>onvif://www.onvif.org/name/Cam1 onvif://www.onvif.org/location/Office</d:Scopes>
    <d:XAddrs>http://192.168.1.20/onvif/device_service</d:XAddrs></d:ProbeMatch></d:ProbeMatches></s:Body></s:Envelope>"""
    found = parse_probe_match(xml)
    assert found == [{"xaddrs": ["http://192.168.1.20/onvif/device_service"],
                      "scopes": ["onvif://www.onvif.org/name/Cam1", "onvif://www.onvif.org/location/Office"],
                      "endpoint": "urn:uuid:1234"}]
    assert parse_probe_match(b"<!DOCTYPE x [<!ENTITY a 'b'>]><x/>") == []


class _NullDetector:
    info = DetectorInfo("null-test-double", "t", "person", "test-double", "n/a")

    def detect(self, frame):
        return [Detection("person", 0.9, (0.1, 0.1, 0.2, 0.5))]


class FlakySource:
    """Fails to open the first ``fail_opens`` times, then delivers ``frames`` frames and drops."""

    opens = 0

    def __init__(self, fail_opens=2, frames=5):
        self.fail_opens, self.frames, self.n = fail_opens, frames, 0

    def open(self):
        FlakySource.opens += 1
        return FlakySource.opens > self.fail_opens

    def read(self):
        self.n += 1
        time.sleep(0.005)
        return np.full((48, 64, 3), 120, np.uint8) if self.n <= self.frames else None

    def close(self):
        pass


def test_worker_reconnects_with_backoff(tmp_path):
    FlakySource.opens = 0
    q = EventQueue(tmp_path / "q.sqlite3")
    cam = {"id": "00000000-0000-0000-0000-000000000001", "name": "test", "zones": [], "privacy_masks": []}
    w = CameraWorker(cam, lambda: FlakySource(), _NullDetector(), q, sample_fps=1000, backoff_initial=0.01,
                     backoff_max=0.05, max_consecutive_failures=3)
    w.start()
    deadline = time.time() + 5
    while time.time() < deadline and w.reconnect_successes < 2:
        time.sleep(0.02)
    w.stop()
    w.join(2)
    assert w.reconnects >= 3 and w.reconnect_successes >= 2 and w.frames > 0
    h = w.health()
    assert set(h) == {"camera_id", "status", "fps", "reconnects", "reconnect_successes", "last_error"}


class FakeClient:
    def __init__(self):
        self.fail = True
        self.received = []

    def post_events(self, events):
        if self.fail:
            raise CloudError("offline")
        self.received += events
        return {"accepted": len(events), "duplicates": 0, "rejected": 0}


def test_sync_keeps_events_during_outage(tmp_path):
    cfg = EdgeConfig(api_url="https://x.example.com", token="zge_t", queue_path=tmp_path / "q.sqlite3")
    client = FakeClient()
    agent = EdgeAgent(cfg, client=client, detector_factory=_NullDetector)
    agent.queue.push({"event_type": "zone_entry"})
    assert agent.sync_once() == -1 and agent.queue.depth() == 1  # outage: retained
    client.fail = False
    assert agent.sync_once() == 1 and agent.queue.depth() == 0
    assert client.received[0]["idempotency_key"]
