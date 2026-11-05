"""Notification channels. Email first; push/SMS are defined interfaces, not yet implemented.

Privacy defaults: alert emails contain NO images, NO bounding boxes and NO video links that
work without login. They include only the incident reference, category, severity, site/camera/
zone names, time, and a link to the authenticated dashboard.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import session_factory
from ..models import Camera, Incident, Membership, Notification, Organisation, Role, Rule, Site, User, Zone

log = logging.getLogger("zoneguard.notify")

SEVERITY_LABELS = {
    "informational": "Informational",
    "review_required": "Review Required",
    "high_priority": "High Priority",
    "critical_review": "Critical Review",
}


@dataclass
class OutboundMessage:
    to: str
    subject: str
    body: str


class Channel(Protocol):
    name: str

    def send(self, msg: OutboundMessage) -> None: ...


class MemoryOutbox:
    """Test/dev outbox — keeps sent messages in memory."""

    def __init__(self) -> None:
        self.messages: list[OutboundMessage] = []
        self._lock = threading.Lock()

    def append(self, m: OutboundMessage) -> None:
        with self._lock:
            self.messages.append(m)

    def clear(self) -> None:
        with self._lock:
            self.messages.clear()


memory_outbox = MemoryOutbox()


class EmailChannel:
    name = "email"

    def send(self, msg: OutboundMessage) -> None:
        s = get_settings()
        if s.email_backend == "memory":
            memory_outbox.append(msg)
            return
        if s.email_backend == "console":
            log.info("EMAIL (console backend) to=%s subject=%s\n%s", msg.to, msg.subject, msg.body)
            memory_outbox.append(msg)
            return
        em = EmailMessage()
        em["From"] = s.email_from
        em["To"] = msg.to
        em["Subject"] = msg.subject
        em.set_content(msg.body)
        ctx = ssl.create_default_context()
        if s.smtp_use_ssl:
            server: smtplib.SMTP = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ctx, timeout=15)
        else:
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15)
        try:
            if s.smtp_starttls and not s.smtp_use_ssl:
                server.starttls(context=ctx)
            if s.smtp_username:
                server.login(s.smtp_username, s.smtp_password)
            server.send_message(em)
        finally:
            try:
                server.quit()
            except smtplib.SMTPException:
                pass


class PushChannel:
    """Interface placeholder. Not implemented in the MVP (requires a mobile app / web push keys)."""

    name = "push"

    def send(self, msg: OutboundMessage) -> None:
        raise NotImplementedError("Push notifications are not implemented in this MVP")


class SmsChannel:
    """Interface placeholder. Not implemented (requires a paid SMS provider and credentials)."""

    name = "sms"

    def send(self, msg: OutboundMessage) -> None:
        raise NotImplementedError("SMS notifications are not implemented in this MVP")


CHANNELS: dict[str, Channel] = {"email": EmailChannel(), "push": PushChannel(), "sms": SmsChannel()}


def resolve_recipients(db: Session, org_id, rule: Rule | None) -> list[User]:
    q = select(User, Membership).join(Membership, Membership.user_id == User.id).where(
        Membership.org_id == org_id, User.is_active.is_(True)
    )
    rows = db.execute(q).all()
    if rule is not None and rule.recipient_user_ids:
        wanted = {str(u) for u in rule.recipient_user_ids}
        # Only org members can receive alerts — ids from other tenants are ignored.
        return [u for u, _m in rows if str(u.id) in wanted]
    return [u for u, m in rows if m.role in (Role.ORG_ADMIN, Role.SITE_MANAGER)]


def compose_incident_email(db: Session, incident: Incident) -> tuple[str, str]:
    org = db.get(Organisation, incident.org_id)
    site = db.get(Site, incident.site_id)
    cam = db.get(Camera, incident.camera_id) if incident.camera_id else None
    zone = db.get(Zone, incident.zone_id) if incident.zone_id else None
    tz = site.timezone if site else (org.timezone if org else "UTC")
    local = incident.occurred_at.astimezone(ZoneInfo(tz))
    sev = SEVERITY_LABELS.get(incident.severity, incident.severity)
    subject = f"[ZoneGuard] {sev}: {incident.title} ({incident.reference})"
    lines = [
        f"A potential incident requires human review.",
        "",
        f"Reference:   {incident.reference}",
        f"Severity:    {sev}",
        f"Category:    {incident.category}",
        f"Site:        {site.name if site else '-'}",
        f"Camera:      {cam.name if cam else '-'}",
        f"Zone:        {zone.name if zone else '-'}",
        f"Time:        {local:%Y-%m-%d %H:%M:%S %Z}",
        f"Rule:        {incident.rule_name or '-'}",
        f"Confidence:  {incident.confidence:.2f}" if incident.confidence is not None else "Confidence:  n/a",
        f"Model:       {incident.model_name} {incident.model_version}".rstrip(),
    ]
    if incident.simulated:
        lines += ["", "NOTE: This incident was produced by a SIMULATED test detector, not a real model."]
    lines += [
        "",
        "Review in the dashboard (login required):",
        f"{get_settings().public_base_url}/incidents/{incident.id}?org={incident.org_id}",
        "",
        "Important: camera AI produces observations, not conclusions. A detection is evidence of",
        "possible activity only and does not establish that any person is unauthorised or acted",
        "wrongfully. A 'Critical Review' severity is a request for urgent human review, not",
        "confirmation that a threat exists. No images are attached to this email by design.",
    ]
    return subject, "\n".join(lines)


def queue_incident_notifications(db: Session, incident: Incident, rule: Rule | None) -> list[Notification]:
    if rule is not None and not rule.notify_email:
        return []
    subject, _ = compose_incident_email(db, incident)
    out = []
    for user in resolve_recipients(db, incident.org_id, rule):
        n = Notification(org_id=incident.org_id, incident_id=incident.id, channel="email",
                         recipient=user.email, subject=subject[:300])
        db.add(n)
        out.append(n)
    return out


def deliver_pending(notification_ids: list | None = None) -> int:
    """Deliver queued notifications. Runs in a background worker with its own DB session."""
    db = session_factory()()
    sent = 0
    try:
        q = select(Notification).where(Notification.status == "queued")
        if notification_ids:
            q = q.where(Notification.id.in_(notification_ids))
        for n in db.scalars(q.limit(200)).all():
            incident = db.get(Incident, n.incident_id) if n.incident_id else None
            if incident is None:
                n.status = "skipped"
                continue
            subject, body = compose_incident_email(db, incident)
            channel = CHANNELS.get(n.channel)
            t0 = time.perf_counter()
            try:
                if channel is None:
                    raise NotImplementedError(f"unknown channel {n.channel}")
                channel.send(OutboundMessage(n.recipient, subject, body))
                n.status = "sent"
                n.sent_at = datetime.now(timezone.utc)
                created = n.created_at if n.created_at.tzinfo else n.created_at.replace(tzinfo=timezone.utc)
                n.latency_ms = (n.sent_at - created).total_seconds() * 1000.0
                sent += 1
            except Exception as exc:  # noqa: BLE001
                n.status = "failed"
                n.error = f"{type(exc).__name__}: {exc}"[:500]
                log.warning("notification %s failed: %s (%.0fms)", n.id, n.error, (time.perf_counter() - t0) * 1000)
            db.commit()
        db.commit()
    finally:
        db.close()
    return sent


def send_plain_email(to: str, subject: str, body: str) -> None:
    CHANNELS["email"].send(OutboundMessage(to, subject, body))
