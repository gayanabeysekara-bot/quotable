from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import EdgeAgent, Membership, Organisation, User, UserSession
from .permissions import Perm, has_perm
from .security import token_hash

SESSION_COOKIE = "zg_session"


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _load_session(request: Request, db: Session) -> UserSession | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or len(token) > 200:
        return None
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash(token)))
    if sess is None or sess.revoked_at is not None:
        return None
    now = datetime.now(timezone.utc)
    idle = timedelta(minutes=get_settings().session_idle_minutes)
    if _aware(sess.expires_at) < now or _aware(sess.last_seen_at) + idle < now:
        return None
    if (now - _aware(sess.last_seen_at)).total_seconds() > 60:
        sess.last_seen_at = now
        db.commit()
    return sess


def get_session_any(request: Request, db: Session = Depends(get_db)) -> UserSession:
    sess = _load_session(request, db)
    if sess is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return sess


def get_current_user(sess: UserSession = Depends(get_session_any), db: Session = Depends(get_db)) -> User:
    if sess.mfa_pending:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA verification required")
    user = db.get(User, sess.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    request_state_user(user)
    return user


def request_state_user(user: User) -> None:  # hook for structured logging
    return None


@dataclass
class OrgContext:
    org: Organisation
    user: User
    role: str

    @property
    def org_id(self) -> uuid.UUID:
        return self.org.id

    def can(self, perm: Perm) -> bool:
        return has_perm(self.role, perm)


def get_org_context(org_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> OrgContext:
    m = db.scalar(select(Membership).where(Membership.org_id == org_id, Membership.user_id == user.id))
    if m is None:
        # Same response whether the org exists or not: do not leak existence of other tenants.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation not found")
    org = db.get(Organisation, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation not found")
    return OrgContext(org=org, user=user, role=m.role)


def require(perm: Perm):
    def dep(ctx: OrgContext = Depends(get_org_context)) -> OrgContext:
        if not ctx.can(perm):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Your role does not permit: {perm.value}")
        return ctx

    return dep


def get_edge_agent(request: Request, db: Session = Depends(get_db)) -> EdgeAgent:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Edge token required")
    token = auth[7:].strip()
    if not token.startswith("zge_") or len(token) > 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid edge token")
    agent = db.scalar(select(EdgeAgent).where(EdgeAgent.token_hash == token_hash(token)))
    if agent is None or agent.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid edge token")
    return agent


def get_owned(db: Session, model, obj_id: uuid.UUID, org_id: uuid.UUID, label: str = "Resource"):
    """Fetch a tenant-owned row, 404 if it belongs to another organisation."""
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, "org_id", None) != org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} not found")
    return obj
