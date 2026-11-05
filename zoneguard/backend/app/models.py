"""SQLAlchemy models.

Tenant hierarchy: Organisation -> Site -> Camera -> Zone -> Rule -> Event -> Incident.
Every tenant-owned table carries ``org_id`` so that every query can (and must) be scoped
by organisation. See app/deps.py for the enforcement point.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> uuid.UUID:
    return uuid.uuid4()


class UTCDateTime(TypeDecorator):
    """Timezone-aware datetime stored as UTC; always returned tz-aware (also on SQLite)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetimes are not allowed; use timezone-aware values")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


TZ = UTCDateTime()


class Role:
    ORG_ADMIN = "org_admin"
    SITE_MANAGER = "site_manager"
    SECURITY_REVIEWER = "security_reviewer"
    AUDITOR = "auditor"
    ALL = (ORG_ADMIN, SITE_MANAGER, SECURITY_REVIEWER, AUDITOR)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mfa_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(TZ)
    revoked_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    ip: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(String(300), default="")


class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    plan: Mapped[str] = mapped_column(String(40), default="pilot")  # subscription-ready
    timezone: Mapped[str] = mapped_column(String(64), default="Australia/Sydney")
    incident_seq: Mapped[int] = mapped_column(Integer, default=0)
    # Feature flags — specialist detectors are OFF by default and opt-in per customer.
    weapon_detection_mode: Mapped[str] = mapped_column(String(40), default="disabled")
    face_covering_mode: Mapped[str] = mapped_column(String(40), default="disabled")
    # Retention (days). Raw uploaded video is short-lived by default.
    video_retention_days: Mapped[int] = mapped_column(Integer, default=7)
    detection_retention_days: Mapped[int] = mapped_column(Integer, default=30)
    event_retention_days: Mapped[int] = mapped_column(Integer, default=90)
    incident_retention_days: Mapped[int] = mapped_column(Integer, default=365)
    audit_retention_days: Mapped[int] = mapped_column(Integer, default=730)
    # Privacy governance records
    surveillance_notice_confirmed_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    surveillance_notice_confirmed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    privacy_contact_email: Mapped[str] = mapped_column(String(320), default="")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("org_id", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)

    user: Mapped[User] = relationship(back_populates="memberships")
    organisation: Mapped[Organisation] = relationship()


class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(40))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TZ)
    accepted_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(400), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="Australia/Sydney")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class EdgeAgent(Base):
    __tablename__ = "edge_agents"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_prefix: Mapped[str] = mapped_column(String(16))
    version: Mapped[str] = mapped_column(String(40), default="")
    last_seen_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    revoked_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    edge_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("edge_agents.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200))
    location_label: Mapped[str] = mapped_column(String(200), default="")
    source_type: Mapped[str] = mapped_column(String(20))  # rtsp | onvif | upload
    stream_url: Mapped[str] = mapped_column(String(1000), default="")  # never contains credentials
    onvif_xaddr: Mapped[str] = mapped_column(String(1000), default="")
    username_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")  # unknown|online|offline|degraded
    last_seen_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    last_error: Mapped[str] = mapped_column(String(500), default="")
    health: Mapped[dict] = mapped_column(JSON, default=dict)
    privacy_masks: Mapped[list] = mapped_column(JSON, default=list)
    snapshot_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)

    site: Mapped[Site] = relationship()


class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10))  # area | line
    points: Mapped[list] = mapped_column(JSON)
    direction: Mapped[str] = mapped_column(String(10), default="any")
    monitoring_schedule: Mapped[list] = mapped_column(JSON, default=list)  # [] = always monitored
    approved_access: Mapped[list] = mapped_column(JSON, default=list)  # windows where entry is approved
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    camera_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True)
    zone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(40))
    schedule: Mapped[list] = mapped_column(JSON, default=list)  # [] = always active
    severity: Mapped[str] = mapped_column(String(30), default="review_required")
    min_confidence: Mapped[float] = mapped_column(Float, default=0.4)
    suppression_seconds: Mapped[int] = mapped_column(Integer, default=300)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    recipient_user_ids: Mapped[list] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class VideoUpload(Base):
    __tablename__ = "video_uploads"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    container: Mapped[str] = mapped_column(String(10), default="")
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    fps: Mapped[float] = mapped_column(Float, default=0)
    duration_s: Mapped[float] = mapped_column(Float, default=0)
    recorded_at: Mapped[datetime] = mapped_column(TZ)
    consent_attested: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_uploads.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(80), default="")
    weapon_mode: Mapped[str] = mapped_column(String(40), default="disabled")
    face_covering_mode: Mapped[str] = mapped_column(String(40), default="disabled")
    sample_fps: Mapped[float] = mapped_column(Float, default=5.0)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str] = mapped_column(String(1000), default="")
    requested_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)


class FrameDetection(Base):
    __tablename__ = "frame_detections"
    __table_args__ = (Index("ix_frame_det_job_offset", "job_id", "offset_s"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"))
    offset_s: Mapped[float] = mapped_column(Float)
    frame_index: Mapped[int] = mapped_column(Integer)
    detections: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("org_id", "idempotency_key"),
        Index("ix_events_org_time", "org_id", "occurred_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"))
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    camera_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True)
    zone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(30))  # upload_analysis | edge | system
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True)
    edge_agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[datetime] = mapped_column(TZ)
    offset_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(String(80), default="")
    model_version: Mapped[str] = mapped_column(String(80), default="")
    model_status: Mapped[str] = mapped_column(String(80), default="")
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_outcome: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class IncidentStatus:
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (Index("ix_incidents_org_status", "org_id", "status"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"))
    reference: Mapped[str] = mapped_column(String(40))
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    camera_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    zone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default=IncidentStatus.OPEN)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(80), default="")
    model_version: Mapped[str] = mapped_column(String(80), default="")
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    rule_name: Mapped[str] = mapped_column(String(200), default="")
    occurred_at: Mapped[datetime] = mapped_column(TZ)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    suppressed_count: Mapped[int] = mapped_column(Integer, default=0)
    last_suppressed_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    resolution_reason: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)


class IncidentHistory(Base):
    __tablename__ = "incident_history"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor_label: Mapped[str] = mapped_column(String(200), default="system")
    action: Mapped[str] = mapped_column(String(40))
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(20), default="email")
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(20), default="queued")
    error: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(TZ, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_org_time", "org_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor_type: Mapped[str] = mapped_column(String(20), default="user")
    actor_label: Mapped[str] = mapped_column(String(320), default="")
    action: Mapped[str] = mapped_column(String(80))
    target_type: Mapped[str] = mapped_column(String(40), default="")
    target_id: Mapped[str] = mapped_column(String(64), default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    detector_task: Mapped[str] = mapped_column(String(40), default="person")
    model_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(80), default="")
    dataset_label: Mapped[str] = mapped_column(String(300), default="")
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=utcnow)
