from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..deps import OrgContext, get_owned, require
from ..models import Camera, Event, Incident, IncidentHistory, Membership, Notification, Site, User, Zone
from ..permissions import Perm
from ..schemas import (
    EventOut,
    HistoryOut,
    IncidentActionIn,
    IncidentAssignIn,
    IncidentNoteIn,
    IncidentOut,
    NotificationOut,
)
from ..services.incidents import add_history, transition

router = APIRouter(prefix="/api/orgs/{org_id}/incidents", tags=["incidents"])


def _enrich(db: Session, incs: list[Incident]) -> list[IncidentOut]:
    sites = {s.id: s.name for s in db.scalars(select(Site).where(Site.id.in_({i.site_id for i in incs})))} if incs else {}
    cam_ids = {i.camera_id for i in incs if i.camera_id}
    zone_ids = {i.zone_id for i in incs if i.zone_id}
    user_ids = {i.assigned_to for i in incs if i.assigned_to}
    cams = {c.id: c.name for c in db.scalars(select(Camera).where(Camera.id.in_(cam_ids)))} if cam_ids else {}
    zones = {z.id: z.name for z in db.scalars(select(Zone).where(Zone.id.in_(zone_ids)))} if zone_ids else {}
    users = {u.id: u.email for u in db.scalars(select(User).where(User.id.in_(user_ids)))} if user_ids else {}
    out = []
    for i in incs:
        o = IncidentOut.model_validate(i)
        o.site_name = sites.get(i.site_id)
        o.camera_name = cams.get(i.camera_id)
        o.zone_name = zones.get(i.zone_id)
        o.assigned_to_email = users.get(i.assigned_to)
        out.append(o)
    return out


@router.get("", response_model=list[IncidentOut])
def list_incidents(status: str | None = None, severity: str | None = None, category: str | None = None,
                   site_id: uuid.UUID | None = None, limit: int = 200,
                   ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    q = select(Incident).where(Incident.org_id == ctx.org_id)
    if status == "active":
        q = q.where(Incident.status.in_(("open", "acknowledged", "escalated")))
    elif status:
        q = q.where(Incident.status == status)
    if severity:
        q = q.where(Incident.severity == severity)
    if category:
        q = q.where(Incident.category == category)
    if site_id:
        q = q.where(Incident.site_id == site_id)
    return _enrich(db, db.scalars(q.order_by(Incident.occurred_at.desc()).limit(min(max(limit, 1), 1000))).all())


@router.get("/export")
def export_incidents(request: Request, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    incs = _enrich(db, db.scalars(select(Incident).where(Incident.org_id == ctx.org_id)
                                  .order_by(Incident.occurred_at.desc()).limit(10000)).all())
    audit.record(db, "incident.exported", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 request=request, details={"count": len(incs)})
    db.commit()
    buf = io.StringIO()
    fields = ["reference", "occurred_at", "status", "severity", "category", "title", "site_name", "camera_name",
              "zone_name", "rule_name", "confidence", "model_name", "model_version", "simulated", "assigned_to_email",
              "suppressed_count", "resolution_reason"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for i in incs:
        d = i.model_dump(mode="json")
        w.writerow({k: ("'" + str(d[k]) if isinstance(d[k], str) and d[k][:1] in "=+-@" else d[k]) for k in fields})
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="zoneguard-incidents.csv"'})


@router.get("/{incident_id}")
def get_incident(incident_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    inc = get_owned(db, Incident, incident_id, ctx.org_id, "Incident")
    history = db.scalars(select(IncidentHistory).where(IncidentHistory.incident_id == inc.id)
                         .order_by(IncidentHistory.created_at)).all()
    notifs = db.scalars(select(Notification).where(Notification.incident_id == inc.id)
                        .order_by(Notification.created_at)).all()
    event = db.get(Event, inc.event_id) if inc.event_id else None
    return {
        "incident": _enrich(db, [inc])[0].model_dump(mode="json"),
        "history": [HistoryOut.model_validate(h).model_dump(mode="json") for h in history],
        "notifications": [NotificationOut.model_validate(n).model_dump(mode="json") for n in notifs],
        "event": EventOut.model_validate(event).model_dump(mode="json") if event else None,
        "disclaimer": "AI detections are observations requiring human judgement. They do not establish that any "
                      "person is unauthorised, dangerous or has committed an offence.",
    }


@router.post("/{incident_id}/actions", response_model=IncidentOut)
def incident_action(incident_id: uuid.UUID, body: IncidentActionIn, request: Request,
                    ctx: OrgContext = Depends(require(Perm.REVIEW_INCIDENTS)), db: Session = Depends(get_db)):
    inc = get_owned(db, Incident, incident_id, ctx.org_id, "Incident")
    frm = inc.status
    transition(db, inc, body.action, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
               note=body.note, reason=body.reason)
    audit.record(db, f"incident.{body.action}", org_id=ctx.org_id, actor_user_id=ctx.user.id,
                 actor_label=ctx.user.email, target_type="incident", target_id=inc.id, request=request,
                 details={"reference": inc.reference, "from": frm, "to": inc.status, "reason": body.reason})
    db.commit()
    return _enrich(db, [inc])[0]


@router.post("/{incident_id}/assign", response_model=IncidentOut)
def assign_incident(incident_id: uuid.UUID, body: IncidentAssignIn, request: Request,
                    ctx: OrgContext = Depends(require(Perm.REVIEW_INCIDENTS)), db: Session = Depends(get_db)):
    inc = get_owned(db, Incident, incident_id, ctx.org_id, "Incident")
    label = "unassigned"
    if body.user_id:
        m = db.scalar(select(Membership).where(Membership.org_id == ctx.org_id, Membership.user_id == body.user_id))
        if m is None:
            raise HTTPException(422, "Assignee must be a member of this organisation")
        label = db.get(User, body.user_id).email
    inc.assigned_to = body.user_id
    inc.updated_at = datetime.now(inc.created_at.tzinfo)
    add_history(db, inc, "assigned", actor_user_id=ctx.user.id, actor_label=ctx.user.email, note=f"Assigned to {label}")
    audit.record(db, "incident.assigned", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="incident", target_id=inc.id, request=request, details={"assignee": label})
    db.commit()
    return _enrich(db, [inc])[0]


@router.post("/{incident_id}/notes", response_model=HistoryOut, status_code=201)
def add_note(incident_id: uuid.UUID, body: IncidentNoteIn, request: Request,
             ctx: OrgContext = Depends(require(Perm.REVIEW_INCIDENTS)), db: Session = Depends(get_db)):
    inc = get_owned(db, Incident, incident_id, ctx.org_id, "Incident")
    h = add_history(db, inc, "note_added", actor_user_id=ctx.user.id, actor_label=ctx.user.email, note=body.note)
    audit.record(db, "incident.note_added", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="incident", target_id=inc.id, request=request)
    db.commit()
    return h
