"""Incident lifecycle: every state change is recorded in incident_history and the audit log."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..models import Incident, IncidentHistory, IncidentStatus, Organisation

S = IncidentStatus

TRANSITIONS: dict[str, dict[str, str]] = {
    # action -> {from_status: to_status}
    "acknowledge": {S.OPEN: S.ACKNOWLEDGED, S.ESCALATED: S.ACKNOWLEDGED},
    "escalate": {S.OPEN: S.ESCALATED, S.ACKNOWLEDGED: S.ESCALATED},
    "dismiss": {S.OPEN: S.DISMISSED, S.ACKNOWLEDGED: S.DISMISSED, S.ESCALATED: S.DISMISSED},
    "close": {S.ACKNOWLEDGED: S.CLOSED, S.ESCALATED: S.CLOSED},
    "reopen": {S.DISMISSED: S.OPEN, S.CLOSED: S.OPEN},
}

DISMISS_REASONS = {"false_positive", "authorised_access", "test_or_staged", "duplicate", "other"}
CLOSE_REASONS = {"resolved", "no_further_action", "referred_externally", "other"}


def next_reference(db: Session, org_id) -> str:
    seq = db.execute(
        update(Organisation)
        .where(Organisation.id == org_id)
        .values(incident_seq=Organisation.incident_seq + 1)
        .returning(Organisation.incident_seq)
    ).scalar_one()
    year = datetime.now(timezone.utc).year
    return f"ZG-{year}-{seq:06d}"


def add_history(db: Session, incident: Incident, action: str, *, actor_user_id=None, actor_label="system",
                from_status=None, to_status=None, note: str = "") -> IncidentHistory:
    h = IncidentHistory(org_id=incident.org_id, incident_id=incident.id, actor_user_id=actor_user_id,
                        actor_label=actor_label, action=action, from_status=from_status, to_status=to_status,
                        note=note[:5000])
    db.add(h)
    return h


def transition(db: Session, incident: Incident, action: str, *, actor_user_id, actor_label: str,
               note: str = "", reason: str = "") -> Incident:
    table = TRANSITIONS.get(action)
    if table is None:
        raise HTTPException(400, f"Unknown action: {action}")
    to = table.get(incident.status)
    if to is None:
        raise HTTPException(409, f"Cannot {action} an incident that is {incident.status}")
    if action == "dismiss":
        if reason not in DISMISS_REASONS:
            raise HTTPException(422, f"Dismissal reason required: one of {sorted(DISMISS_REASONS)}")
    if action == "close":
        reason = reason or "resolved"
        if reason not in CLOSE_REASONS:
            raise HTTPException(422, f"Closure reason must be one of {sorted(CLOSE_REASONS)}")
    now = datetime.now(timezone.utc)
    frm = incident.status
    incident.status = to
    incident.updated_at = now
    if to in (S.CLOSED, S.DISMISSED):
        incident.closed_at = now
        incident.resolution_reason = reason
    elif action == "reopen":
        incident.closed_at = None
        incident.resolution_reason = ""
    full_note = (f"[{reason}] " if reason else "") + (note or "")
    add_history(db, incident, action, actor_user_id=actor_user_id, actor_label=actor_label,
                from_status=frm, to_status=to, note=full_note.strip())
    return incident
