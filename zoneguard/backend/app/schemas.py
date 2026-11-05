"""Pydantic request/response schemas. Response models never include secrets or credentials."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import Role
from .services import schedules
from .services.rule_engine import EVENT_TYPES, SEVERITIES

RoleName = Literal["org_admin", "site_manager", "security_reviewer", "auditor"]
Severity = Literal["informational", "review_required", "high_priority", "critical_review"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    full_name: str = Field(min_length=1, max_length=200)
    organisation_name: str = Field(min_length=2, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class MfaCodeIn(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class MembershipOut(BaseModel):
    org_id: uuid.UUID
    org_name: str
    role: str


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    mfa_enabled: bool
    memberships: list[MembershipOut]


# ---------- organisation ----------
class OrgOut(ORM):
    id: uuid.UUID
    name: str
    plan: str
    timezone: str
    weapon_detection_mode: str
    face_covering_mode: str
    video_retention_days: int
    detection_retention_days: int
    event_retention_days: int
    incident_retention_days: int
    audit_retention_days: int
    surveillance_notice_confirmed_at: datetime | None
    privacy_contact_email: str


class OrgUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    timezone: str | None = None
    weapon_detection_mode: Literal["disabled", "simulated_test", "coco_knife_unvalidated"] | None = None
    face_covering_mode: Literal["disabled", "simulated_test"] | None = None
    video_retention_days: int | None = Field(default=None, ge=1, le=90)
    detection_retention_days: int | None = Field(default=None, ge=1, le=365)
    event_retention_days: int | None = Field(default=None, ge=1, le=1095)
    incident_retention_days: int | None = Field(default=None, ge=30, le=2555)
    audit_retention_days: int | None = Field(default=None, ge=365, le=3650)
    privacy_contact_email: EmailStr | None = None
    confirm_surveillance_notice: bool | None = None

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v):
        return v if v is None else schedules.validate_timezone(v)


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    mfa_enabled: bool


class MemberRoleUpdate(BaseModel):
    role: RoleName


class InviteIn(BaseModel):
    email: EmailStr
    role: RoleName


class InviteOut(ORM):
    id: uuid.UUID
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class AcceptInviteIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=256)


# ---------- sites ----------
class SiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=400)
    timezone: str = "Australia/Sydney"

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v):
        return schedules.validate_timezone(v)


class SiteOut(ORM):
    id: uuid.UUID
    name: str
    address: str
    timezone: str
    created_at: datetime


# ---------- cameras ----------
Point = tuple[float, float]


def _validate_polys(v: list[list[Point]]) -> list[list[Point]]:
    from zoneguard_vision.geometry import validate_polygon

    if len(v) > 16:
        raise ValueError("at most 16 privacy masks")
    return [validate_polygon(p) for p in v]


def _validate_stream_url(v: str) -> str:
    if not v:
        return v
    parts = urlsplit(v)
    if parts.scheme not in ("rtsp", "rtsps", "http", "https"):
        raise ValueError("stream URL must use rtsp, rtsps, http or https")
    if parts.username or parts.password or "@" in parts.netloc:
        raise ValueError("do not embed credentials in the URL; use the username/password fields")
    if not parts.hostname:
        raise ValueError("stream URL must include a host")
    return v


class CameraIn(BaseModel):
    site_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    location_label: str = Field(default="", max_length=200)
    source_type: Literal["rtsp", "onvif", "upload"]
    stream_url: str = Field(default="", max_length=1000)
    onvif_xaddr: str = Field(default="", max_length=1000)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=200)
    edge_agent_id: uuid.UUID | None = None
    privacy_masks: list[list[Point]] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("stream_url", "onvif_xaddr")
    @classmethod
    def _v_url(cls, v):
        return _validate_stream_url(v)

    @field_validator("privacy_masks")
    @classmethod
    def _v_masks(cls, v):
        return _validate_polys(v)


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    location_label: str | None = Field(default=None, max_length=200)
    stream_url: str | None = Field(default=None, max_length=1000)
    onvif_xaddr: str | None = Field(default=None, max_length=1000)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=200)
    clear_credentials: bool = False
    edge_agent_id: uuid.UUID | None = None
    privacy_masks: list[list[Point]] | None = None
    enabled: bool | None = None

    @field_validator("stream_url", "onvif_xaddr")
    @classmethod
    def _v_url(cls, v):
        return v if v is None else _validate_stream_url(v)

    @field_validator("privacy_masks")
    @classmethod
    def _v_masks(cls, v):
        return v if v is None else _validate_polys(v)


class CameraOut(ORM):
    id: uuid.UUID
    site_id: uuid.UUID
    edge_agent_id: uuid.UUID | None
    name: str
    location_label: str
    source_type: str
    stream_url: str
    onvif_xaddr: str
    has_credentials: bool = False
    enabled: bool
    status: str
    last_seen_at: datetime | None
    last_error: str
    health: dict
    privacy_masks: list
    has_snapshot: bool = False
    created_at: datetime


# ---------- zones ----------
class ZoneIn(BaseModel):
    camera_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    kind: Literal["area", "line"]
    points: list[Point]
    direction: Literal["any", "a_to_b", "b_to_a"] = "any"
    monitoring_schedule: list[dict] = Field(default_factory=list)
    approved_access: list[dict] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("monitoring_schedule", "approved_access")
    @classmethod
    def _sched(cls, v):
        return schedules.validate_windows(v)

    def validated_points(self) -> list[Point]:
        from zoneguard_vision.geometry import validate_polygon

        if self.kind == "line":
            if len(self.points) != 2:
                raise ValueError("an entrance boundary needs exactly 2 points")
            return validate_polygon(self.points, min_points=2)
        return validate_polygon(self.points)


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    points: list[Point] | None = None
    direction: Literal["any", "a_to_b", "b_to_a"] | None = None
    monitoring_schedule: list[dict] | None = None
    approved_access: list[dict] | None = None
    enabled: bool | None = None

    @field_validator("monitoring_schedule", "approved_access")
    @classmethod
    def _sched(cls, v):
        return v if v is None else schedules.validate_windows(v)


class ZoneOut(ORM):
    id: uuid.UUID
    camera_id: uuid.UUID
    name: str
    kind: str
    points: list
    direction: str
    monitoring_schedule: list
    approved_access: list
    enabled: bool
    created_at: datetime


# ---------- rules ----------
class RuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_type: Literal[EVENT_TYPES]  # type: ignore[valid-type]
    site_id: uuid.UUID | None = None
    camera_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    schedule: list[dict] = Field(default_factory=list)
    severity: Severity = "review_required"
    min_confidence: float = Field(default=0.4, ge=0.0, le=1.0)
    suppression_seconds: int = Field(default=300, ge=0, le=86400)
    notify_email: bool = True
    recipient_user_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    enabled: bool = True

    @field_validator("schedule")
    @classmethod
    def _sched(cls, v):
        return schedules.validate_windows(v)


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    schedule: list[dict] | None = None
    severity: Severity | None = None
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    suppression_seconds: int | None = Field(default=None, ge=0, le=86400)
    notify_email: bool | None = None
    recipient_user_ids: list[uuid.UUID] | None = Field(default=None, max_length=50)
    enabled: bool | None = None

    @field_validator("schedule")
    @classmethod
    def _sched(cls, v):
        return v if v is None else schedules.validate_windows(v)


class RuleOut(ORM):
    id: uuid.UUID
    name: str
    event_type: str
    site_id: uuid.UUID | None
    camera_id: uuid.UUID | None
    zone_id: uuid.UUID | None
    schedule: list
    severity: str
    min_confidence: float
    suppression_seconds: int
    notify_email: bool
    recipient_user_ids: list
    enabled: bool
    created_at: datetime


# ---------- videos / analysis ----------
class VideoOut(ORM):
    id: uuid.UUID
    site_id: uuid.UUID
    camera_id: uuid.UUID
    original_filename: str
    size_bytes: int
    sha256: str
    container: str
    width: int
    height: int
    fps: float
    duration_s: float
    recorded_at: datetime
    consent_attested: bool
    created_at: datetime
    deleted_at: datetime | None


class AnalysisIn(BaseModel):
    model_name: str = "yolox_tiny"
    sample_fps: float = Field(default=5.0, ge=0.5, le=15.0)
    weapon_mode: Literal["disabled", "simulated_test", "coco_knife_unvalidated"] = "disabled"
    face_covering_mode: Literal["disabled", "simulated_test"] = "disabled"


class AnalysisJobOut(ORM):
    id: uuid.UUID
    video_id: uuid.UUID
    status: str
    progress: float
    model_name: str
    model_version: str
    weapon_mode: str
    face_covering_mode: str
    sample_fps: float
    stats: dict
    error: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


# ---------- events / incidents ----------
class EventOut(ORM):
    id: uuid.UUID
    site_id: uuid.UUID
    camera_id: uuid.UUID | None
    zone_id: uuid.UUID | None
    source: str
    job_id: uuid.UUID | None
    event_type: str
    occurred_at: datetime
    offset_s: float | None
    track_id: int | None
    confidence: float | None
    bbox: list | None
    model_name: str
    model_version: str
    model_status: str
    simulated: bool
    attributes: dict
    rule_outcome: str


class IncidentOut(ORM):
    id: uuid.UUID
    reference: str
    org_id: uuid.UUID
    site_id: uuid.UUID
    camera_id: uuid.UUID | None
    zone_id: uuid.UUID | None
    rule_id: uuid.UUID | None
    event_id: uuid.UUID | None
    title: str
    category: str
    severity: str
    status: str
    confidence: float | None
    model_name: str
    model_version: str
    simulated: bool
    rule_name: str
    occurred_at: datetime
    assigned_to: uuid.UUID | None
    suppressed_count: int
    resolution_reason: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    site_name: str | None = None
    camera_name: str | None = None
    zone_name: str | None = None
    assigned_to_email: str | None = None


class HistoryOut(ORM):
    id: uuid.UUID
    actor_label: str
    action: str
    from_status: str | None
    to_status: str | None
    note: str
    created_at: datetime


class IncidentActionIn(BaseModel):
    action: Literal["acknowledge", "escalate", "dismiss", "close", "reopen"]
    note: str = Field(default="", max_length=5000)
    reason: str = Field(default="", max_length=60)


class IncidentAssignIn(BaseModel):
    user_id: uuid.UUID | None


class IncidentNoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=5000)


class NotificationOut(ORM):
    id: uuid.UUID
    channel: str
    recipient: str
    subject: str
    status: str
    error: str
    created_at: datetime
    sent_at: datetime | None
    latency_ms: float | None


class AuditOut(ORM):
    id: uuid.UUID
    actor_type: str
    actor_label: str
    action: str
    target_type: str
    target_id: str
    ip: str
    details: dict
    created_at: datetime


# ---------- edge ----------
class EdgeAgentIn(BaseModel):
    site_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)


class EdgeAgentOut(ORM):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str
    token_prefix: str
    version: str
    last_seen_at: datetime | None
    stats: dict
    revoked_at: datetime | None
    created_at: datetime


class EdgeEventIn(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=120)
    camera_id: uuid.UUID
    zone_id: uuid.UUID | None = None
    event_type: Literal[EVENT_TYPES]  # type: ignore[valid-type]
    occurred_at: datetime
    track_id: int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    bbox: list[float] | None = Field(default=None, max_length=4)
    model_name: str = Field(default="", max_length=80)
    model_version: str = Field(default="", max_length=80)
    model_status: str = Field(default="", max_length=80)
    simulated: bool = False
    attributes: dict = Field(default_factory=dict)

    @field_validator("attributes")
    @classmethod
    def _attrs(cls, v: dict):
        if len(str(v)) > 2000:
            raise ValueError("attributes too large")
        return v


class EdgeEventsIn(BaseModel):
    events: list[EdgeEventIn] = Field(max_length=500)


class CameraHealthIn(BaseModel):
    camera_id: uuid.UUID
    status: Literal["online", "offline", "degraded"]
    fps: float | None = None
    reconnects: int | None = None
    reconnect_successes: int | None = None
    last_error: str = Field(default="", max_length=500)


class EdgeHeartbeatIn(BaseModel):
    version: str = Field(default="", max_length=40)
    queue_depth: int = 0
    cpu_percent: float | None = None
    rss_mb: float | None = None
    cameras: list[CameraHealthIn] = Field(default_factory=list, max_length=128)


class EvaluationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    detector_task: Literal["person", "weapon", "face_covering"] = "person"
    model_name: str = Field(max_length=80)
    model_version: str = Field(default="", max_length=80)
    dataset_label: str = Field(default="", max_length=300)
    metrics: dict


class EvaluationOut(ORM):
    id: uuid.UUID
    name: str
    detector_task: str
    model_name: str
    model_version: str
    dataset_label: str
    metrics: dict
    created_at: datetime


__all__ = [n for n in dir() if n[0].isupper()] + ["Role", "SEVERITIES"]
