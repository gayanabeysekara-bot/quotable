"""Edge agent API.

* Org-scoped management endpoints (create / list / revoke agents) use the user session.
* Agent endpoints (/api/edge/*) use a per-agent bearer token (stored only as a SHA-256 hash).
  Agents receive camera credentials for their own site only, over TLS, and send back
  event METADATA only — never video frames (snapshots only when an admin requests a preview).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..deps import OrgContext, get_edge_agent, get_owned, require
from ..models import Camera, EdgeAgent, Event, Organisation, Site, Zone
from ..permissions import Perm
from ..schemas import EdgeAgentIn, EdgeAgentOut, EdgeEventsIn, EdgeHeartbeatIn
from ..security import decrypt_secret, new_token, token_hash
from ..services import dispatch, storage
from ..services.notifications import deliver_pending
from ..services.rule_engine import evaluate_event

mgmt = APIRouter(prefix="/api/orgs/{org_id}/edge-agents", tags=["edge management"])
agent_api = APIRouter(prefix="/api/edge", tags=["edge agent"])

OFFLINE_AFTER_S = 120


@mgmt.get("", response_model=list[EdgeAgentOut])
def list_agents(ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return db.scalars(select(EdgeAgent).where(EdgeAgent.org_id == ctx.org_id).order_by(EdgeAgent.created_at)).all()


@mgmt.post("", status_code=201)
def create_agent(body: EdgeAgentIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_EDGE)),
                 db: Session = Depends(get_db)):
    get_owned(db, Site, body.site_id, ctx.org_id, "Site")
    token = new_token("zge_")
    agent = EdgeAgent(org_id=ctx.org_id, site_id=body.site_id, name=body.name, token_hash=token_hash(token),
                      token_prefix=token[:10])
    db.add(agent)
    db.flush()
    audit.record(db, "edge.agent_created", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="edge_agent", target_id=agent.id, request=request, details={"name": body.name})
    db.commit()
    return {"agent": EdgeAgentOut.model_validate(agent).model_dump(mode="json"), "token": token,
            "warning": "Copy this token now. It is shown only once and stored only as a hash."}


@mgmt.post("/{agent_id}/rotate-token")
def rotate_agent_token(agent_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_EDGE)),
                       db: Session = Depends(get_db)):
    agent = get_owned(db, EdgeAgent, agent_id, ctx.org_id, "Edge agent")
    token = new_token("zge_")
    agent.token_hash, agent.token_prefix = token_hash(token), token[:10]
    audit.record(db, "edge.token_rotated", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="edge_agent", target_id=agent.id, request=request)
    db.commit()
    return {"token": token}


@mgmt.delete("/{agent_id}")
def revoke_agent(agent_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_EDGE)),
                 db: Session = Depends(get_db)):
    agent = get_owned(db, EdgeAgent, agent_id, ctx.org_id, "Edge agent")
    agent.revoked_at = datetime.now(timezone.utc)
    audit.record(db, "edge.agent_revoked", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="edge_agent", target_id=agent.id, request=request)
    db.commit()
    return {"ok": True}


# ---------------- agent-authenticated ----------------
@agent_api.get("/config")
def edge_config(request: Request, agent: EdgeAgent = Depends(get_edge_agent), db: Session = Depends(get_db)):
    org = db.get(Organisation, agent.org_id)
    site = db.get(Site, agent.site_id)
    cams = db.scalars(select(Camera).where(Camera.org_id == agent.org_id, Camera.site_id == agent.site_id,
                                           Camera.source_type.in_(("rtsp", "onvif")), Camera.enabled.is_(True),
                                           (Camera.edge_agent_id == agent.id) | (Camera.edge_agent_id.is_(None)))).all()
    out = []
    for c in cams:
        zones = db.scalars(select(Zone).where(Zone.camera_id == c.id, Zone.enabled.is_(True))).all()
        out.append({
            "id": str(c.id), "name": c.name, "source_type": c.source_type, "stream_url": c.stream_url,
            "onvif_xaddr": c.onvif_xaddr, "username": decrypt_secret(c.username_enc),
            "password": decrypt_secret(c.password_enc), "privacy_masks": c.privacy_masks or [],
            "zones": [{"id": str(z.id), "name": z.name, "kind": z.kind, "points": z.points, "direction": z.direction}
                      for z in zones],
        })
    audit.record(db, "edge.config_fetched", org_id=agent.org_id, actor_type="edge", actor_label=agent.name,
                 target_type="edge_agent", target_id=agent.id, request=request, details={"cameras": len(out)})
    db.commit()
    return {"agent_id": str(agent.id), "site": {"id": str(site.id), "name": site.name, "timezone": site.timezone},
            "features": {"weapon_detection_mode": org.weapon_detection_mode,
                         "face_covering_mode": org.face_covering_mode},
            "cameras": out}


@agent_api.post("/heartbeat")
def edge_heartbeat(body: EdgeHeartbeatIn, agent: EdgeAgent = Depends(get_edge_agent), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    agent.last_seen_at = now
    agent.version = body.version
    stats = dict(agent.stats or {})
    stats.update({"queue_depth": body.queue_depth, "cpu_percent": body.cpu_percent, "rss_mb": body.rss_mb})
    attempts = successes = 0
    created = []
    for ch in body.cameras:
        cam = db.get(Camera, ch.camera_id)
        if cam is None or cam.org_id != agent.org_id or cam.site_id != agent.site_id:
            continue  # ignore cameras outside this agent's tenant/site
        prev = cam.status
        cam.status = ch.status
        cam.last_error = ch.last_error
        cam.health = {"fps": ch.fps, "reconnects": ch.reconnects, "reconnect_successes": ch.reconnect_successes,
                      "reported_at": now.isoformat()}
        attempts += ch.reconnects or 0
        successes += ch.reconnect_successes or 0
        if ch.status == "online":
            cam.last_seen_at = now
        if ch.status == "offline" and prev != "offline":
            created += _system_event(db, cam, "camera_offline", now, agent.id, {"error": ch.last_error})
    stats["reconnect_attempts"] = attempts
    stats["reconnect_successes"] = successes
    agent.stats = stats
    db.commit()
    if created:
        dispatch.submit(deliver_pending)
    return {"ok": True, "server_time": now.isoformat()}


def _system_event(db: Session, cam: Camera, event_type: str, when: datetime, agent_id, attrs: dict) -> list:
    e = Event(org_id=cam.org_id, site_id=cam.site_id, camera_id=cam.id, source="system", edge_agent_id=agent_id,
              event_type=event_type, occurred_at=when, model_name="camera-health", model_version="1",
              model_status="system", attributes=attrs)
    db.add(e)
    db.flush()
    return evaluate_event(db, e)


@agent_api.post("/events")
def edge_events(body: EdgeEventsIn, request: Request, agent: EdgeAgent = Depends(get_edge_agent),
                db: Session = Depends(get_db)):
    """Idempotent batch ingest of event metadata buffered by the agent (safe to retry after outages)."""
    accepted = duplicates = rejected = incidents = 0
    now = datetime.now(timezone.utc)
    for ev in body.events:
        cam = db.get(Camera, ev.camera_id)
        if cam is None or cam.org_id != agent.org_id or cam.site_id != agent.site_id:
            rejected += 1
            continue
        if ev.zone_id:
            z = db.get(Zone, ev.zone_id)
            if z is None or z.camera_id != cam.id:
                rejected += 1
                continue
        if ev.occurred_at.tzinfo is None or ev.occurred_at > now + timedelta(minutes=5):
            rejected += 1
            continue
        key = f"{agent.id}:{ev.idempotency_key}"
        if db.scalar(select(Event.id).where(Event.org_id == agent.org_id, Event.idempotency_key == key)):
            duplicates += 1
            continue
        e = Event(org_id=agent.org_id, site_id=cam.site_id, camera_id=cam.id, zone_id=ev.zone_id, source="edge",
                  edge_agent_id=agent.id, idempotency_key=key, event_type=ev.event_type, occurred_at=ev.occurred_at,
                  track_id=ev.track_id, confidence=ev.confidence, bbox=ev.bbox, model_name=ev.model_name,
                  model_version=ev.model_version, model_status=ev.model_status, simulated=ev.simulated,
                  attributes=ev.attributes)
        try:
            with db.begin_nested():
                db.add(e)
                db.flush()
        except IntegrityError:
            duplicates += 1
            continue
        incidents += len(evaluate_event(db, e))
        accepted += 1
    agent.last_seen_at = now
    db.commit()
    if incidents:
        dispatch.submit(deliver_pending)
    return {"accepted": accepted, "duplicates": duplicates, "rejected": rejected, "incidents_created": incidents}


@agent_api.post("/discovery")
def edge_discovery(devices: list[dict], agent: EdgeAgent = Depends(get_edge_agent), db: Session = Depends(get_db)):
    clean = []
    for d in devices[:64]:
        clean.append({"xaddrs": [str(x)[:300] for x in (d.get("xaddrs") or [])][:4],
                      "scopes": [str(x)[:200] for x in (d.get("scopes") or [])][:10],
                      "endpoint": str(d.get("endpoint", ""))[:200]})
    stats = dict(agent.stats or {})
    stats["onvif_discovered"] = clean
    stats["onvif_discovered_at"] = datetime.now(timezone.utc).isoformat()
    agent.stats = stats
    db.commit()
    return {"ok": True, "count": len(clean)}


@agent_api.post("/cameras/{camera_id}/snapshot")
async def edge_snapshot(camera_id: uuid.UUID, file: UploadFile = File(...), agent: EdgeAgent = Depends(get_edge_agent),
                        db: Session = Depends(get_db)):
    """Store a single privacy-masked still for zone drawing (agent masks before sending)."""
    cam = db.get(Camera, camera_id)
    if cam is None or cam.org_id != agent.org_id or cam.site_id != agent.site_id:
        raise HTTPException(404, "Camera not found")
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Snapshot too large")
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(415, "Snapshot must be a JPEG or PNG image")
    ok, buf = cv2.imencode(".jpg", img)  # re-encode: strips metadata and any non-image payload
    storage.delete(cam.snapshot_key)
    cam.snapshot_key = storage.new_key(cam.org_id, ".jpg")
    p = storage.path_for(cam.snapshot_key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(buf.tobytes())
    db.commit()
    return {"ok": True}


def sweep_stale_cameras(db: Session) -> int:
    """Mark edge cameras offline if their agent stopped reporting; raises camera_offline events."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=OFFLINE_AFTER_S)
    n = 0
    for cam in db.scalars(select(Camera).where(Camera.source_type.in_(("rtsp", "onvif")),
                                               Camera.status.in_(("online", "degraded")))).all():
        seen = cam.last_seen_at
        if seen is not None and (seen if seen.tzinfo else seen.replace(tzinfo=timezone.utc)) < cutoff:
            cam.status = "offline"
            cam.last_error = "No heartbeat from edge agent"
            _system_event(db, cam, "camera_offline", datetime.now(timezone.utc), cam.edge_agent_id,
                          {"error": "heartbeat timeout"})
            n += 1
    db.commit()
    return n
