"""Retention & deletion. Raw uploaded footage is deleted after the org's video retention period."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import audit
from ..models import AuditLog, Event, FrameDetection, Incident, Organisation, UserSession, VideoUpload
from . import storage

log = logging.getLogger("zoneguard.retention")


def purge_video(db: Session, video: VideoUpload) -> None:
    storage.delete(video.storage_key)
    video.storage_key = None
    video.deleted_at = datetime.now(timezone.utc)


def sweep_org(db: Session, org: Organisation, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    counts = {"videos": 0, "frame_detections": 0, "events": 0, "incidents": 0, "audit_logs": 0}
    for v in db.scalars(select(VideoUpload).where(
        VideoUpload.org_id == org.id, VideoUpload.deleted_at.is_(None),
        VideoUpload.created_at < now - timedelta(days=org.video_retention_days),
    )).all():
        purge_video(db, v)
        counts["videos"] += 1
    counts["frame_detections"] = db.execute(delete(FrameDetection).where(
        FrameDetection.org_id == org.id,
        FrameDetection.created_at < now - timedelta(days=org.detection_retention_days))).rowcount or 0
    # Closed/dismissed incidents past retention are removed (history cascades).
    counts["incidents"] = db.execute(delete(Incident).where(
        Incident.org_id == org.id, Incident.status.in_(("closed", "dismissed")),
        Incident.closed_at < now - timedelta(days=org.incident_retention_days))).rowcount or 0
    # Events still referenced by an active incident are kept.
    active_event_ids = select(Incident.event_id).where(Incident.org_id == org.id, Incident.event_id.is_not(None))
    counts["events"] = db.execute(delete(Event).where(
        Event.org_id == org.id, Event.created_at < now - timedelta(days=org.event_retention_days),
        Event.id.not_in(active_event_ids))).rowcount or 0
    counts["audit_logs"] = db.execute(delete(AuditLog).where(
        AuditLog.org_id == org.id, AuditLog.created_at < now - timedelta(days=org.audit_retention_days))).rowcount or 0
    if any(counts.values()):
        audit.record(db, "retention.sweep", org_id=org.id, actor_type="system", actor_label="retention",
                     details=counts)
    return counts


def sweep_all(db: Session) -> dict:
    total: dict[str, int] = {}
    for org in db.scalars(select(Organisation)).all():
        for k, v in sweep_org(db, org).items():
            total[k] = total.get(k, 0) + v
    db.execute(delete(UserSession).where(UserSession.expires_at < datetime.now(timezone.utc) - timedelta(days=1)))
    db.commit()
    return total
