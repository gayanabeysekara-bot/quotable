"""Security alert engine: Detection event -> rule evaluation -> potential incident -> notification.

Principles enforced here:
* A detection is evidence of *possible* activity. Incident titles never state that a person is
  unauthorised, dangerous or criminal.
* Face-covering observations are neutral: rules for them are capped at "informational" and a
  face covering never raises the severity of another incident.
* Weapon observations are "possible objects". Nothing here triggers any automatic external action
  (no emergency calls, no lockdowns, no access-control changes). Humans decide.
* Repeated events within a rule's suppression window are folded into the open incident.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera, Event, Incident, Organisation, Rule, Site, Zone
from . import schedules
from .incidents import add_history, next_reference
from .notifications import queue_incident_notifications

log = logging.getLogger("zoneguard.rules")

SEVERITIES = ("informational", "review_required", "high_priority", "critical_review")
EVENT_TYPES = (
    "zone_entry",
    "line_crossing",
    "weapon_possible",
    "face_covering_observed",
    "camera_offline",
    "camera_obstructed",
)
ZONE_EVENTS = {"zone_entry", "line_crossing"}
MAX_SEVERITY = {"face_covering_observed": "informational"}
ACTIVE = ("open", "acknowledged", "escalated")


def cap_severity(event_type: str, severity: str) -> str:
    cap = MAX_SEVERITY.get(event_type)
    if cap and SEVERITIES.index(severity) > SEVERITIES.index(cap):
        return cap
    return severity


def _title(event: Event, zone: Zone | None, camera: Camera | None) -> str:
    where = zone.name if zone else (camera.name if camera else "camera")
    t = event.event_type
    sim = "SIMULATED: " if event.simulated else ""
    if t == "zone_entry":
        return f"{sim}Person detected entering {where}"
    if t == "line_crossing":
        return f"{sim}Person detected crossing {where} boundary"
    if t == "weapon_possible":
        label = (event.attributes or {}).get("label", "object")
        return f"{sim}Possible {label.replace('possible ', '').replace('SIMULATED ', '')} observed — needs review"
    if t == "face_covering_observed":
        return f"{sim}Face covering observed (neutral observation)"
    if t == "camera_offline":
        return f"Camera offline: {camera.name if camera else '-'}"
    if t == "camera_obstructed":
        return f"Camera view possibly obstructed: {camera.name if camera else '-'}"
    return f"{sim}{t}"


def _matching_rules(db: Session, event: Event) -> list[Rule]:
    rules = db.scalars(
        select(Rule).where(Rule.org_id == event.org_id, Rule.enabled.is_(True), Rule.event_type == event.event_type)
    ).all()
    out = []
    for r in rules:
        if r.site_id and r.site_id != event.site_id:
            continue
        if r.camera_id and r.camera_id != event.camera_id:
            continue
        if r.zone_id and r.zone_id != event.zone_id:
            continue
        out.append(r)
    return out


def evaluate_event(db: Session, event: Event) -> list[Incident]:
    """Evaluate one persisted event. Caller commits. Returns newly created incidents."""
    site = db.get(Site, event.site_id)
    org = db.get(Organisation, event.org_id)
    tz = site.timezone if site else (org.timezone if org else "UTC")
    zone = db.get(Zone, event.zone_id) if event.zone_id else None
    camera = db.get(Camera, event.camera_id) if event.camera_id else None

    # Customer-level feature gates: disabled specialist modules never create incidents.
    if event.event_type == "weapon_possible" and org and org.weapon_detection_mode == "disabled":
        event.rule_outcome = "weapon_detection_disabled_for_org"
        return []
    if event.event_type == "face_covering_observed" and org and org.face_covering_mode == "disabled":
        event.rule_outcome = "face_covering_disabled_for_org"
        return []

    if event.event_type in ZONE_EVENTS and zone is not None:
        if not zone.enabled or not schedules.matches(zone.monitoring_schedule, event.occurred_at, tz):
            event.rule_outcome = "zone_not_monitored_at_this_time"
            return []
        if zone.approved_access and schedules.matches(zone.approved_access, event.occurred_at, tz):
            event.rule_outcome = "within_approved_access_period"
            return []

    created: list[Incident] = []
    outcomes: list[str] = []
    for rule in _matching_rules(db, event):
        if event.confidence is not None and event.confidence < rule.min_confidence:
            outcomes.append(f"{rule.name}:below_min_confidence")
            continue
        if not schedules.matches(rule.schedule, event.occurred_at, tz):
            outcomes.append(f"{rule.name}:outside_rule_schedule")
            continue
        window = timedelta(seconds=max(0, rule.suppression_seconds))
        existing = None
        if window.total_seconds() > 0:
            existing = db.scalar(
                select(Incident)
                .where(
                    Incident.org_id == event.org_id,
                    Incident.rule_id == rule.id,
                    Incident.camera_id == event.camera_id,
                    Incident.zone_id == event.zone_id,
                    Incident.status.in_(ACTIVE),
                    Incident.occurred_at >= event.occurred_at - window,
                    Incident.occurred_at <= event.occurred_at + window,
                )
                .order_by(Incident.occurred_at.desc())
                .limit(1)
            )
        if existing is not None:
            existing.suppressed_count += 1
            existing.last_suppressed_at = event.occurred_at
            outcomes.append(f"{rule.name}:suppressed_into_{existing.reference}")
            continue
        incident = Incident(
            org_id=event.org_id,
            reference=next_reference(db, event.org_id),
            site_id=event.site_id,
            camera_id=event.camera_id,
            zone_id=event.zone_id,
            rule_id=rule.id,
            event_id=event.id,
            title=_title(event, zone, camera)[:300],
            category=event.event_type,
            severity=cap_severity(event.event_type, rule.severity),
            confidence=event.confidence,
            model_name=event.model_name,
            model_version=event.model_version,
            simulated=event.simulated,
            rule_name=rule.name,
            occurred_at=event.occurred_at,
        )
        db.add(incident)
        db.flush()
        add_history(db, incident, "created", to_status="open",
                    note=f"Rule '{rule.name}' triggered by {event.source} event {event.id}")
        queue_incident_notifications(db, incident, rule)
        created.append(incident)
        outcomes.append(f"{rule.name}:incident_{incident.reference}")
    event.rule_outcome = ("; ".join(outcomes) or "no_matching_rule")[:200]
    return created
