from __future__ import annotations

import logging
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog

log = logging.getLogger("zoneguard.audit")

_SENSITIVE = {"password", "password_enc", "username_enc", "token", "secret", "mfa_secret", "username"}


def _scrub(details: dict | None) -> dict:
    out = {}
    for k, v in (details or {}).items():
        out[k] = "[redacted]" if k.lower() in _SENSITIVE else v
    return out


def record(
    db: Session,
    action: str,
    *,
    org_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    actor_label: str = "",
    actor_type: str = "user",
    target_type: str = "",
    target_id: object = "",
    request: Request | None = None,
    details: dict | None = None,
) -> AuditLog:
    from .ratelimit import client_ip

    entry = AuditLog(
        org_id=org_id,
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        actor_label=actor_label,
        action=action,
        target_type=target_type,
        target_id=str(target_id or ""),
        ip=client_ip(request) if request is not None else "",
        details=_scrub(details),
    )
    db.add(entry)
    log.info("audit action=%s org=%s actor=%s target=%s:%s", action, org_id, actor_label, target_type, target_id)
    return entry
