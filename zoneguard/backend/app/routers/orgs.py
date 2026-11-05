from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..deps import OrgContext, get_org_context, get_owned, require
from ..models import (
    AuditLog,
    Camera,
    EdgeAgent,
    Event,
    Incident,
    Invitation,
    Membership,
    Notification,
    Role,
    Site,
    User,
    Zone,
)
from ..permissions import ROLE_PERMISSIONS, Perm
from ..schemas import (
    AuditOut,
    InviteIn,
    InviteOut,
    MemberOut,
    MemberRoleUpdate,
    OrgOut,
    OrgUpdate,
    SiteIn,
    SiteOut,
)
from ..security import new_token, token_hash
from ..services import retention
from ..services.notifications import send_plain_email
from ..config import get_settings

router = APIRouter(prefix="/api/orgs/{org_id}", tags=["organisation"])


@router.get("", response_model=OrgOut)
def get_org(ctx: OrgContext = Depends(require(Perm.VIEW))):
    return ctx.org


@router.get("/me")
def my_role(ctx: OrgContext = Depends(get_org_context)):
    return {"role": ctx.role, "permissions": sorted(p.value for p in ROLE_PERMISSIONS.get(ctx.role, set()))}


@router.patch("", response_model=OrgOut)
def update_org(body: OrgUpdate, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ORG)),
               db: Session = Depends(get_db)):
    org = db.merge(ctx.org)
    changes = body.model_dump(exclude_unset=True)
    confirm = changes.pop("confirm_surveillance_notice", None)
    for k, v in changes.items():
        setattr(org, k, v)
    if confirm:
        org.surveillance_notice_confirmed_at = datetime.now(timezone.utc)
        org.surveillance_notice_confirmed_by = ctx.user.id
    audit.record(db, "org.settings_updated", org_id=org.id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="organisation", target_id=org.id, request=request,
                 details={**changes, **({"surveillance_notice_confirmed": True} if confirm else {})})
    db.commit()
    return org


# ---------------- members & invitations ----------------
@router.get("/members", response_model=list[MemberOut])
def list_members(ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    rows = db.execute(select(Membership, User).join(User, User.id == Membership.user_id)
                      .where(Membership.org_id == ctx.org_id).order_by(User.email)).all()
    return [MemberOut(user_id=u.id, email=u.email, full_name=u.full_name, role=m.role, mfa_enabled=u.mfa_enabled)
            for m, u in rows]


def _admin_count(db: Session, org_id) -> int:
    return db.scalar(select(func.count()).select_from(Membership).where(
        Membership.org_id == org_id, Membership.role == Role.ORG_ADMIN)) or 0


@router.patch("/members/{user_id}")
def update_member(user_id: uuid.UUID, body: MemberRoleUpdate, request: Request,
                  ctx: OrgContext = Depends(require(Perm.MANAGE_MEMBERS)), db: Session = Depends(get_db)):
    m = db.scalar(select(Membership).where(Membership.org_id == ctx.org_id, Membership.user_id == user_id))
    if m is None:
        raise HTTPException(404, "Member not found")
    if m.role == Role.ORG_ADMIN and body.role != Role.ORG_ADMIN and _admin_count(db, ctx.org_id) <= 1:
        raise HTTPException(409, "An organisation must keep at least one administrator")
    old = m.role
    m.role = body.role
    audit.record(db, "member.role_changed", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="user", target_id=user_id, request=request, details={"from": old, "to": body.role})
    db.commit()
    return {"ok": True}


@router.delete("/members/{user_id}")
def remove_member(user_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_MEMBERS)),
                  db: Session = Depends(get_db)):
    m = db.scalar(select(Membership).where(Membership.org_id == ctx.org_id, Membership.user_id == user_id))
    if m is None:
        raise HTTPException(404, "Member not found")
    if m.role == Role.ORG_ADMIN and _admin_count(db, ctx.org_id) <= 1:
        raise HTTPException(409, "An organisation must keep at least one administrator")
    db.delete(m)
    audit.record(db, "member.removed", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="user", target_id=user_id, request=request)
    db.commit()
    return {"ok": True}


@router.get("/invitations", response_model=list[InviteOut])
def list_invitations(ctx: OrgContext = Depends(require(Perm.MANAGE_MEMBERS)), db: Session = Depends(get_db)):
    return db.scalars(select(Invitation).where(Invitation.org_id == ctx.org_id)
                      .order_by(Invitation.created_at.desc()).limit(200)).all()


@router.post("/invitations", status_code=201)
def create_invitation(body: InviteIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_MEMBERS)),
                      db: Session = Depends(get_db)):
    from ..ratelimit import enforce

    enforce(request, "invite", 30, 3600, key_extra=str(ctx.org_id))
    email = body.email.lower()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user and db.scalar(select(Membership).where(Membership.org_id == ctx.org_id,
                                                            Membership.user_id == existing_user.id)):
        raise HTTPException(409, "That person is already a member")
    token = new_token()
    inv = Invitation(org_id=ctx.org_id, email=email, role=body.role, token_hash=token_hash(token),
                     invited_by=ctx.user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    db.add(inv)
    db.flush()
    link = f"{get_settings().public_base_url}/accept-invite?token={token}"
    audit.record(db, "member.invited", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="invitation", target_id=inv.id, request=request, details={"email": email, "role": body.role})
    db.commit()
    delivered = True
    try:
        send_plain_email(email, f"You've been invited to {ctx.org.name} on ZoneGuard AI",
                         f"{ctx.user.full_name or ctx.user.email} invited you to join {ctx.org.name} on ZoneGuard AI "
                         f"as {body.role.replace('_', ' ')}.\n\nAccept within 7 days:\n{link}\n\n"
                         "If you were not expecting this, you can ignore this email.")
    except Exception:  # noqa: BLE001
        delivered = False
    # The link is returned to the inviting admin so invitations work even before SMTP is configured.
    return {"id": str(inv.id), "invite_link": link, "email_delivered": delivered}


@router.delete("/invitations/{inv_id}")
def revoke_invitation(inv_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_MEMBERS)),
                      db: Session = Depends(get_db)):
    inv = get_owned(db, Invitation, inv_id, ctx.org_id, "Invitation")
    inv.revoked_at = datetime.now(timezone.utc)
    audit.record(db, "member.invitation_revoked", org_id=ctx.org_id, actor_user_id=ctx.user.id,
                 actor_label=ctx.user.email, target_type="invitation", target_id=inv.id, request=request)
    db.commit()
    return {"ok": True}


# ---------------- sites ----------------
@router.get("/sites", response_model=list[SiteOut])
def list_sites(ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return db.scalars(select(Site).where(Site.org_id == ctx.org_id).order_by(Site.name)).all()


@router.post("/sites", response_model=SiteOut, status_code=201)
def create_site(body: SiteIn, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_SITES)),
                db: Session = Depends(get_db)):
    site = Site(org_id=ctx.org_id, **body.model_dump())
    db.add(site)
    db.flush()
    audit.record(db, "site.created", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="site", target_id=site.id, request=request, details={"name": site.name})
    db.commit()
    return site


@router.patch("/sites/{site_id}", response_model=SiteOut)
def update_site(site_id: uuid.UUID, body: SiteIn, request: Request,
                ctx: OrgContext = Depends(require(Perm.MANAGE_SITES)), db: Session = Depends(get_db)):
    site = get_owned(db, Site, site_id, ctx.org_id, "Site")
    for k, v in body.model_dump().items():
        setattr(site, k, v)
    audit.record(db, "site.updated", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="site", target_id=site.id, request=request)
    db.commit()
    return site


@router.delete("/sites/{site_id}")
def delete_site(site_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ORG)),
                db: Session = Depends(get_db)):
    site = get_owned(db, Site, site_id, ctx.org_id, "Site")
    db.delete(site)
    audit.record(db, "site.deleted", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="site", target_id=site_id, request=request, details={"name": site.name})
    db.commit()
    return {"ok": True}


# ---------------- audit, overview, retention ----------------
@router.get("/audit", response_model=list[AuditOut])
def list_audit(limit: int = 200, action: str | None = None, ctx: OrgContext = Depends(require(Perm.VIEW_AUDIT)),
               db: Session = Depends(get_db)):
    q = select(AuditLog).where(AuditLog.org_id == ctx.org_id)
    if action:
        q = q.where(AuditLog.action.startswith(action))
    return db.scalars(q.order_by(AuditLog.created_at.desc()).limit(min(max(limit, 1), 1000))).all()


@router.get("/overview")
def overview(site_id: uuid.UUID | None = None, ctx: OrgContext = Depends(require(Perm.VIEW)),
             db: Session = Depends(get_db)):
    def scoped(q, model):
        q = q.where(model.org_id == ctx.org_id)
        if site_id is not None and hasattr(model, "site_id"):
            q = q.where(model.site_id == site_id)
        return q

    cams = db.scalars(scoped(select(Camera), Camera)).all()
    cam_ids = [c.id for c in cams]
    zones = db.scalar(select(func.count()).select_from(Zone).where(Zone.org_id == ctx.org_id,
                                                                   Zone.camera_id.in_(cam_ids) if cam_ids else false())) or 0
    active = db.scalar(scoped(select(func.count()).select_from(Incident), Incident).where(
        Incident.status.in_(("open", "acknowledged", "escalated")))) or 0
    by_sev = dict(db.execute(scoped(select(Incident.severity, func.count()), Incident).where(
        Incident.status.in_(("open", "acknowledged", "escalated"))).group_by(Incident.severity)).all())
    since = datetime.now(timezone.utc) - timedelta(days=14)
    inc_recent = db.scalars(scoped(select(Incident), Incident).where(Incident.created_at >= since)).all()
    trend: dict[str, int] = {}
    for i in range(14):
        d = (datetime.now(timezone.utc) - timedelta(days=13 - i)).date().isoformat()
        trend[d] = 0
    for inc in inc_recent:
        d = (inc.created_at if inc.created_at.tzinfo else inc.created_at.replace(tzinfo=timezone.utc)).date().isoformat()
        if d in trend:
            trend[d] += 1
    recent_events = db.scalars(scoped(select(Event), Event).order_by(Event.occurred_at.desc()).limit(10)).all()
    edge = db.scalars(select(EdgeAgent).where(EdgeAgent.org_id == ctx.org_id, EdgeAgent.revoked_at.is_(None))).all()
    return {
        "cameras": {
            "total": len(cams),
            "online": sum(1 for c in cams if c.status == "online"),
            "offline": sum(1 for c in cams if c.status == "offline"),
            "degraded": sum(1 for c in cams if c.status == "degraded"),
            "unknown": sum(1 for c in cams if c.status == "unknown"),
            "items": [{"id": str(c.id), "name": c.name, "status": c.status, "source_type": c.source_type,
                       "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None} for c in cams],
        },
        "zones": zones,
        "active_incidents": active,
        "active_by_severity": by_sev,
        "incident_trend": [{"date": k, "count": v} for k, v in trend.items()],
        "recent_events": [{"id": str(e.id), "event_type": e.event_type, "occurred_at": e.occurred_at.isoformat(),
                           "confidence": e.confidence, "camera_id": str(e.camera_id) if e.camera_id else None,
                           "simulated": e.simulated, "rule_outcome": e.rule_outcome} for e in recent_events],
        "edge_agents": [{"id": str(a.id), "name": a.name,
                         "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None} for a in edge],
        "privacy": {"surveillance_notice_confirmed": ctx.org.surveillance_notice_confirmed_at is not None,
                    "weapon_detection_mode": ctx.org.weapon_detection_mode,
                    "face_covering_mode": ctx.org.face_covering_mode},
    }


@router.get("/metrics")
def operational_metrics(days: int = 30, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    """Operational metrics derived from REAL review outcomes and delivery logs (no invented numbers)."""
    days = min(max(days, 1), 365)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    incs = db.scalars(select(Incident).where(Incident.org_id == ctx.org_id, Incident.created_at >= since)).all()
    reviewed = [i for i in incs if i.status in ("dismissed", "closed", "acknowledged", "escalated")]
    false_alerts = [i for i in incs if i.status == "dismissed" and i.resolution_reason == "false_positive"]
    cams = db.scalar(select(func.count()).select_from(Camera).where(Camera.org_id == ctx.org_id)) or 0
    notifs = db.scalars(select(Notification).where(Notification.org_id == ctx.org_id,
                                                   Notification.created_at >= since)).all()
    lat = sorted(n.latency_ms for n in notifs if n.latency_ms is not None)
    per_cat: dict[str, dict] = {}
    for i in incs:
        c = per_cat.setdefault(i.category, {"incidents": 0, "dismissed_false_positive": 0, "confirmed_relevant": 0})
        c["incidents"] += 1
        if i in false_alerts:
            c["dismissed_false_positive"] += 1
        if i.status in ("escalated", "closed") or (i.status == "acknowledged"):
            c["confirmed_relevant"] += 1
    agents = db.scalars(select(EdgeAgent).where(EdgeAgent.org_id == ctx.org_id)).all()
    rec_attempts = sum(int((a.stats or {}).get("reconnect_attempts", 0)) for a in agents)
    rec_ok = sum(int((a.stats or {}).get("reconnect_successes", 0)) for a in agents)
    return {
        "window_days": days,
        "incidents": len(incs),
        "reviewed": len(reviewed),
        "dismissed_false_positive": len(false_alerts),
        "reviewer_precision": round(1 - len(false_alerts) / len(reviewed), 3) if reviewed else None,
        "false_alerts_per_camera_per_day": round(len(false_alerts) / cams / days, 4) if cams else None,
        "per_category": per_cat,
        "notifications": {"sent": sum(1 for n in notifs if n.status == "sent"),
                          "failed": sum(1 for n in notifs if n.status == "failed"),
                          "p50_latency_ms": lat[len(lat) // 2] if lat else None,
                          "p95_latency_ms": lat[int(0.95 * (len(lat) - 1))] if lat else None},
        "camera_reconnects": {"attempts": rec_attempts, "successes": rec_ok,
                              "success_rate": round(rec_ok / rec_attempts, 3) if rec_attempts else None},
        "note": "Reviewer precision reflects human review outcomes, not independent ground truth. "
                "Recall cannot be measured from alerts alone — use the evaluation framework.",
    }


@router.post("/retention/run")
def run_retention(request: Request, ctx: OrgContext = Depends(require(Perm.MANAGE_ORG)), db: Session = Depends(get_db)):
    org = db.merge(ctx.org)
    counts = retention.sweep_org(db, org)
    audit.record(db, "retention.manual_run", org_id=ctx.org_id, actor_user_id=ctx.user.id,
                 actor_label=ctx.user.email, request=request, details=counts)
    db.commit()
    return counts
