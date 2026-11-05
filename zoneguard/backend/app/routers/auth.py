from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..config import get_settings
from ..db import get_db
from ..deps import SESSION_COOKIE, get_current_user, get_session_any
from ..models import Invitation, Membership, Organisation, Role, User, UserSession
from ..ratelimit import client_ip, enforce
from ..schemas import AcceptInviteIn, LoginIn, MeOut, MembershipOut, MfaCodeIn, PasswordChangeIn, RegisterIn
from ..security import (
    decrypt_secret,
    encrypt_secret,
    hash_password,
    needs_rehash,
    new_token,
    new_totp_secret,
    token_hash,
    totp_uri,
    validate_password_strength,
    verify_password,
    verify_totp,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOCKOUT_THRESHOLD = 8
LOCKOUT_MINUTES = 15


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _start_session(db: Session, response: Response, request: Request, user: User, mfa_pending: bool) -> None:
    s = get_settings()
    token = new_token()
    db.add(UserSession(
        user_id=user.id, token_hash=token_hash(token), mfa_pending=mfa_pending,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=s.session_ttl_hours),
        ip=client_ip(request), user_agent=request.headers.get("user-agent", "")[:300],
    ))
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=s.cookie_secure, samesite="strict",
        max_age=s.session_ttl_hours * 3600, path="/",
    )


def _me(db: Session, user: User) -> MeOut:
    rows = db.execute(
        select(Membership, Organisation).join(Organisation, Organisation.id == Membership.org_id)
        .where(Membership.user_id == user.id).order_by(Organisation.name)
    ).all()
    return MeOut(id=user.id, email=user.email, full_name=user.full_name, mfa_enabled=user.mfa_enabled,
                 memberships=[MembershipOut(org_id=o.id, org_name=o.name, role=m.role) for m, o in rows])


@router.post("/register", response_model=MeOut, status_code=201)
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    """Self-service organisation registration. The registering user becomes org administrator."""
    enforce(request, "register", 5, 3600)
    try:
        validate_password_strength(body.password)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists. Sign in instead.")
    user = User(email=email, full_name=body.full_name.strip(), password_hash=hash_password(body.password))
    org = Organisation(name=body.organisation_name.strip(), privacy_contact_email=email)
    db.add_all([user, org])
    db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role=Role.ORG_ADMIN))
    audit.record(db, "org.registered", org_id=org.id, actor_user_id=user.id, actor_label=email,
                 target_type="organisation", target_id=org.id, request=request)
    _start_session(db, response, request, user, mfa_pending=False)
    db.commit()
    return _me(db, user)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    email = body.email.lower()
    enforce(request, "login", s.rate_limit_login_per_minute, 60)
    enforce(request, "login-acct", s.rate_limit_login_per_minute, 60, key_extra=email)
    user = db.scalar(select(User).where(User.email == email))
    now = datetime.now(timezone.utc)
    if user and user.locked_until and _aware(user.locked_until) > now:
        verify_password(body.password, None)  # keep timing similar
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    ok = verify_password(body.password, user.password_hash if user else None)
    if not user or not ok or not user.is_active:
        if user:
            user.failed_logins += 1
            if user.failed_logins >= LOCKOUT_THRESHOLD:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_logins = 0
            audit.record(db, "auth.login_failed", actor_user_id=user.id, actor_label=email, request=request)
            db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    user.failed_logins = 0
    user.locked_until = None
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    _start_session(db, response, request, user, mfa_pending=user.mfa_enabled)
    if not user.mfa_enabled:
        user.last_login_at = now
    audit.record(db, "auth.login" if not user.mfa_enabled else "auth.login_password_ok_mfa_pending",
                 actor_user_id=user.id, actor_label=email, request=request)
    db.commit()
    if user.mfa_enabled:
        return {"mfa_required": True}
    return {"mfa_required": False, "user": _me(db, user).model_dump(mode="json")}


@router.post("/mfa/verify")
def mfa_verify(body: MfaCodeIn, request: Request, sess: UserSession = Depends(get_session_any),
               db: Session = Depends(get_db)):
    enforce(request, "mfa", 10, 60, key_extra=str(sess.user_id))
    user = db.get(User, sess.user_id)
    if not sess.mfa_pending:
        return {"ok": True}
    secret = decrypt_secret(user.mfa_secret_enc) if user and user.mfa_secret_enc else None
    if not secret or not verify_totp(secret, body.code):
        audit.record(db, "auth.mfa_failed", actor_user_id=sess.user_id, actor_label=user.email if user else "",
                     request=request)
        db.commit()
        raise HTTPException(401, "Invalid verification code")
    sess.mfa_pending = False
    user.last_login_at = datetime.now(timezone.utc)
    audit.record(db, "auth.login", actor_user_id=user.id, actor_label=user.email, request=request,
                 details={"mfa": True})
    db.commit()
    return {"ok": True, "user": _me(db, user).model_dump(mode="json")}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sess = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash(token)))
        if sess and sess.revoked_at is None:
            sess.revoked_at = datetime.now(timezone.utc)
            audit.record(db, "auth.logout", actor_user_id=sess.user_id, request=request)
            db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _me(db, user)


@router.post("/password")
def change_password(body: PasswordChangeIn, request: Request, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    enforce(request, "pwchange", 5, 300, key_extra=str(user.id))
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    try:
        validate_password_strength(body.new_password)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    user.password_hash = hash_password(body.new_password)
    # Revoke all other sessions
    current = token_hash(request.cookies.get(SESSION_COOKIE, ""))
    for s in db.scalars(select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))):
        if s.token_hash != current:
            s.revoked_at = datetime.now(timezone.utc)
    audit.record(db, "auth.password_changed", actor_user_id=user.id, actor_label=user.email, request=request)
    db.commit()
    return {"ok": True}


@router.post("/mfa/setup")
def mfa_setup(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Begin TOTP enrolment. MFA is enabled only after a valid code is confirmed."""
    if user.mfa_enabled:
        raise HTTPException(409, "MFA already enabled")
    secret = new_totp_secret()
    user.mfa_secret_enc = encrypt_secret(secret)
    db.commit()
    return {"secret": secret, "otpauth_uri": totp_uri(secret, user.email)}


@router.post("/mfa/enable")
def mfa_enable(body: MfaCodeIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = decrypt_secret(user.mfa_secret_enc)
    if not secret or not verify_totp(secret, body.code):
        raise HTTPException(400, "Invalid verification code")
    user.mfa_enabled = True
    audit.record(db, "auth.mfa_enabled", actor_user_id=user.id, actor_label=user.email, request=request)
    db.commit()
    return {"ok": True}


@router.post("/mfa/disable")
def mfa_disable(body: MfaCodeIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = decrypt_secret(user.mfa_secret_enc)
    if not user.mfa_enabled or not secret or not verify_totp(secret, body.code):
        raise HTTPException(400, "Invalid verification code")
    user.mfa_enabled = False
    user.mfa_secret_enc = None
    audit.record(db, "auth.mfa_disabled", actor_user_id=user.id, actor_label=user.email, request=request)
    db.commit()
    return {"ok": True}


@router.post("/invitations/accept")
def accept_invitation(body: AcceptInviteIn, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce(request, "invite-accept", 10, 600)
    inv = db.scalar(select(Invitation).where(Invitation.token_hash == token_hash(body.token)))
    now = datetime.now(timezone.utc)
    if inv is None or inv.accepted_at or inv.revoked_at or _aware(inv.expires_at) < now:
        raise HTTPException(400, "This invitation is invalid or has expired")
    user = db.scalar(select(User).where(User.email == inv.email))
    if user is None:
        if not body.password or not body.full_name:
            raise HTTPException(422, "Full name and password are required to create your account")
        try:
            validate_password_strength(body.password)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        user = User(email=inv.email, full_name=body.full_name.strip(), password_hash=hash_password(body.password))
        db.add(user)
        db.flush()
    else:
        # Existing account: must prove ownership with their password.
        if not body.password or not verify_password(body.password, user.password_hash):
            raise HTTPException(401, "Enter your existing ZoneGuard password to accept")
    if not db.scalar(select(Membership).where(Membership.org_id == inv.org_id, Membership.user_id == user.id)):
        db.add(Membership(org_id=inv.org_id, user_id=user.id, role=inv.role))
    inv.accepted_at = now
    audit.record(db, "member.invitation_accepted", org_id=inv.org_id, actor_user_id=user.id,
                 actor_label=user.email, target_type="invitation", target_id=inv.id, request=request,
                 details={"role": inv.role})
    _start_session(db, response, request, user, mfa_pending=user.mfa_enabled)
    db.commit()
    return {"ok": True, "org_id": str(inv.org_id), "mfa_required": user.mfa_enabled}
