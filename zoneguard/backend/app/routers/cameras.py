from __future__ import annotations

import uuid

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..deps import OrgContext, get_owned, require
from ..models import Camera, EdgeAgent, Rule, Site, VideoUpload, Zone
from ..permissions import Perm
from ..schemas import CameraIn, CameraOut, CameraUpdate, RuleIn, RuleOut, RuleUpdate, ZoneIn, ZoneOut, ZoneUpdate
from ..security import encrypt_secret
from ..services import storage

router = APIRouter(prefix="/api/orgs/{org_id}", tags=["cameras"])


def camera_out(c: Camera) -> CameraOut:
    out = CameraOut.model_validate(c)
    out.has_credentials = bool(c.username_enc or c.password_enc)
    out.has_snapshot = bool(c.snapshot_key)
    return out


def _check_edge(db: Session, ctx: OrgContext, edge_agent_id, site_id):
    if edge_agent_id is None:
        return
    agent = get_owned(db, EdgeAgent, edge_agent_id, ctx.org_id, "Edge agent")
    if agent.site_id != site_id:
        raise HTTPException(422, "Edge agent belongs to a different site")


@router.get("/cameras", response_model=list[CameraOut])
def list_cameras(site_id: uuid.UUID | None = None, ctx: OrgContext = Depends(require(Perm.VIEW)),
                 db: Session = Depends(get_db)):
    q = select(Camera).where(Camera.org_id == ctx.org_id)
    if site_id:
        q = q.where(Camera.site_id == site_id)
    return [camera_out(c) for c in db.scalars(q.order_by(Camera.name)).all()]


@router.get("/cameras/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return camera_out(get_owned(db, Camera, camera_id, ctx.org_id, "Camera"))


@router.post("/cameras", response_model=CameraOut, status_code=201)
def create_camera(body: CameraIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_CAMERAS)),
                  db: Session = Depends(get_db)):
    get_owned(db, Site, body.site_id, ctx.org_id, "Site")
    _check_edge(db, ctx, body.edge_agent_id, body.site_id)
    if body.source_type == "rtsp" and not body.stream_url:
        raise HTTPException(422, "RTSP cameras require a stream URL")
    if body.source_type == "onvif" and not (body.onvif_xaddr or body.stream_url):
        raise HTTPException(422, "ONVIF cameras require a device service address or stream URL")
    cam = Camera(
        org_id=ctx.org_id, site_id=body.site_id, edge_agent_id=body.edge_agent_id, name=body.name,
        location_label=body.location_label, source_type=body.source_type, stream_url=body.stream_url,
        onvif_xaddr=body.onvif_xaddr, username_enc=encrypt_secret(body.username),
        password_enc=encrypt_secret(body.password), privacy_masks=[list(map(list, m)) for m in body.privacy_masks],
        enabled=body.enabled,
    )
    db.add(cam)
    db.flush()
    audit.record(db, "camera.created", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="camera", target_id=cam.id, request=request,
                 details={"name": cam.name, "source_type": cam.source_type, "credentials_set": bool(body.password)})
    db.commit()
    return camera_out(cam)


@router.patch("/cameras/{camera_id}", response_model=CameraOut)
def update_camera(camera_id: uuid.UUID, body: CameraUpdate, request: Request,
                  ctx: OrgContext = Depends(require(Perm.MANAGE_CAMERAS)), db: Session = Depends(get_db)):
    cam = get_owned(db, Camera, camera_id, ctx.org_id, "Camera")
    data = body.model_dump(exclude_unset=True)
    changed = []
    if "edge_agent_id" in data:
        _check_edge(db, ctx, data["edge_agent_id"], cam.site_id)
    for k in ("name", "location_label", "stream_url", "onvif_xaddr", "edge_agent_id", "enabled"):
        if k in data:
            setattr(cam, k, data[k])
            changed.append(k)
    if "privacy_masks" in data and data["privacy_masks"] is not None:
        cam.privacy_masks = [list(map(list, m)) for m in data["privacy_masks"]]
        changed.append("privacy_masks")
    if data.get("clear_credentials"):
        cam.username_enc = cam.password_enc = None
        changed.append("credentials_cleared")
    else:
        if data.get("username") is not None:
            cam.username_enc = encrypt_secret(data["username"])
            changed.append("username")
        if data.get("password") is not None:
            cam.password_enc = encrypt_secret(data["password"])
            changed.append("password")
    audit.record(db, "camera.updated", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="camera", target_id=cam.id, request=request, details={"fields": changed})
    db.commit()
    return camera_out(cam)


@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_CAMERAS)),
                  db: Session = Depends(get_db)):
    cam = get_owned(db, Camera, camera_id, ctx.org_id, "Camera")
    for v in db.scalars(select(VideoUpload).where(VideoUpload.camera_id == cam.id)).all():
        storage.delete(v.storage_key)
    storage.delete(cam.snapshot_key)
    db.delete(cam)
    audit.record(db, "camera.deleted", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="camera", target_id=camera_id, request=request, details={"name": cam.name})
    db.commit()
    return {"ok": True}


@router.get("/cameras/{camera_id}/snapshot")
def camera_snapshot(camera_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    """Privacy-masked still used for zone drawing. Requires authentication and org membership."""
    from zoneguard_vision.privacy import apply_privacy_masks
    from zoneguard_vision.video import read_frame_at

    cam = get_owned(db, Camera, camera_id, ctx.org_id, "Camera")
    frame = None
    if cam.snapshot_key:
        p = storage.path_for(cam.snapshot_key)
        if p.exists():
            frame = cv2.imdecode(np.frombuffer(p.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        v = db.scalar(select(VideoUpload).where(VideoUpload.camera_id == cam.id, VideoUpload.deleted_at.is_(None))
                      .order_by(VideoUpload.created_at.desc()).limit(1))
        if v and v.storage_key:
            frame = read_frame_at(storage.path_for(v.storage_key), min(1.0, v.duration_s / 2))
    if frame is None:
        raise HTTPException(404, "No preview available yet. Upload a video or connect the edge agent.")
    frame = apply_privacy_masks(frame, [[tuple(p) for p in m] for m in cam.privacy_masks or []])
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return Response(buf.tobytes(), media_type="image/jpeg", headers={"Cache-Control": "private, no-store"})


# ---------------- zones ----------------
@router.get("/zones", response_model=list[ZoneOut])
def list_zones(camera_id: uuid.UUID | None = None, ctx: OrgContext = Depends(require(Perm.VIEW)),
               db: Session = Depends(get_db)):
    q = select(Zone).where(Zone.org_id == ctx.org_id)
    if camera_id:
        q = q.where(Zone.camera_id == camera_id)
    return db.scalars(q.order_by(Zone.name)).all()


@router.post("/zones", response_model=ZoneOut, status_code=201)
def create_zone(body: ZoneIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)),
                db: Session = Depends(get_db)):
    get_owned(db, Camera, body.camera_id, ctx.org_id, "Camera")
    try:
        pts = body.validated_points()
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    z = Zone(org_id=ctx.org_id, camera_id=body.camera_id, name=body.name, kind=body.kind,
             points=[list(p) for p in pts], direction=body.direction,
             monitoring_schedule=body.monitoring_schedule, approved_access=body.approved_access, enabled=body.enabled)
    db.add(z)
    db.flush()
    audit.record(db, "zone.created", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="zone", target_id=z.id, request=request, details={"name": z.name, "kind": z.kind})
    db.commit()
    return z


@router.patch("/zones/{zone_id}", response_model=ZoneOut)
def update_zone(zone_id: uuid.UUID, body: ZoneUpdate, request: Request,
                ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)), db: Session = Depends(get_db)):
    from zoneguard_vision.geometry import validate_polygon

    z = get_owned(db, Zone, zone_id, ctx.org_id, "Zone")
    data = body.model_dump(exclude_unset=True)
    if data.get("points") is not None:
        try:
            pts = validate_polygon(data["points"], min_points=2 if z.kind == "line" else 3)
            if z.kind == "line" and len(pts) != 2:
                raise ValueError("an entrance boundary needs exactly 2 points")
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        z.points = [list(p) for p in pts]
    for k in ("name", "direction", "monitoring_schedule", "approved_access", "enabled"):
        if k in data and data[k] is not None:
            setattr(z, k, data[k])
    audit.record(db, "zone.updated", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="zone", target_id=z.id, request=request, details={"fields": list(data)})
    db.commit()
    return z


@router.delete("/zones/{zone_id}")
def delete_zone(zone_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)),
                db: Session = Depends(get_db)):
    z = get_owned(db, Zone, zone_id, ctx.org_id, "Zone")
    db.delete(z)
    audit.record(db, "zone.deleted", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="zone", target_id=zone_id, request=request, details={"name": z.name})
    db.commit()
    return {"ok": True}


# ---------------- rules ----------------
def _check_rule_scope(db: Session, ctx: OrgContext, site_id, camera_id, zone_id):
    if site_id:
        get_owned(db, Site, site_id, ctx.org_id, "Site")
    if camera_id:
        cam = get_owned(db, Camera, camera_id, ctx.org_id, "Camera")
        if site_id and cam.site_id != site_id:
            raise HTTPException(422, "Camera is not in the selected site")
    if zone_id:
        z = get_owned(db, Zone, zone_id, ctx.org_id, "Zone")
        if camera_id and z.camera_id != camera_id:
            raise HTTPException(422, "Zone is not on the selected camera")


def _check_recipients(db: Session, ctx: OrgContext, ids):
    from ..models import Membership

    if not ids:
        return
    members = {m for (m,) in db.execute(select(Membership.user_id).where(Membership.org_id == ctx.org_id)).all()}
    bad = [str(i) for i in ids if i not in members]
    if bad:
        raise HTTPException(422, "Recipients must be members of this organisation")


@router.get("/rules", response_model=list[RuleOut])
def list_rules(ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return db.scalars(select(Rule).where(Rule.org_id == ctx.org_id).order_by(Rule.name)).all()


@router.post("/rules", response_model=RuleOut, status_code=201)
def create_rule(body: RuleIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)),
                db: Session = Depends(get_db)):
    from ..services.rule_engine import cap_severity

    _check_rule_scope(db, ctx, body.site_id, body.camera_id, body.zone_id)
    _check_recipients(db, ctx, body.recipient_user_ids)
    data = body.model_dump()
    data["severity"] = cap_severity(body.event_type, body.severity)
    data["recipient_user_ids"] = [str(u) for u in body.recipient_user_ids]
    r = Rule(org_id=ctx.org_id, created_by=ctx.user.id, **data)
    db.add(r)
    db.flush()
    audit.record(db, "rule.created", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="rule", target_id=r.id, request=request,
                 details={"name": r.name, "event_type": r.event_type, "severity": r.severity})
    db.commit()
    return r


@router.patch("/rules/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: uuid.UUID, body: RuleUpdate, request: Request,
                ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)), db: Session = Depends(get_db)):
    from ..services.rule_engine import cap_severity

    r = get_owned(db, Rule, rule_id, ctx.org_id, "Rule")
    data = body.model_dump(exclude_unset=True)
    if data.get("recipient_user_ids") is not None:
        _check_recipients(db, ctx, data["recipient_user_ids"])
        data["recipient_user_ids"] = [str(u) for u in data["recipient_user_ids"]]
    if data.get("severity"):
        data["severity"] = cap_severity(r.event_type, data["severity"])
    for k, v in data.items():
        if v is not None:
            setattr(r, k, v)
    audit.record(db, "rule.updated", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="rule", target_id=r.id, request=request, details={"fields": list(data)})
    db.commit()
    return r


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ZONES_RULES)),
                db: Session = Depends(get_db)):
    r = get_owned(db, Rule, rule_id, ctx.org_id, "Rule")
    db.delete(r)
    audit.record(db, "rule.deleted", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="rule", target_id=rule_id, request=request, details={"name": r.name})
    db.commit()
    return {"ok": True}
