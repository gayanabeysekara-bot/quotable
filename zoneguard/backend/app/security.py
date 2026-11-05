"""Password hashing, opaque session tokens, secret encryption and TOTP (MFA)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from functools import lru_cache

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from .config import get_settings

_hasher = PasswordHasher()  # Argon2id with library defaults (RFC 9106 low-memory profile)
_DUMMY_HASH = _hasher.hash("timing-equaliser-not-a-password")

MIN_PASSWORD_LENGTH = 12


def validate_password_strength(pw: str) -> None:
    if len(pw) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(pw) > 256:
        raise ValueError("password too long")
    if pw.lower() == pw or pw.upper() == pw or not any(c.isdigit() for c in pw):
        raise ValueError("password must contain upper and lower case letters and a digit")


def hash_password(pw: str) -> str:
    return _hasher.hash(pw)


def verify_password(pw: str, hashed: str | None) -> bool:
    try:
        return _hasher.verify(hashed or _DUMMY_HASH, pw) and hashed is not None
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def new_token(prefix: str = "") -> str:
    return prefix + secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


@lru_cache
def _fernet() -> MultiFernet:
    keys = [k.strip() for k in get_settings().encryption_keys.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("ZG_ENCRYPTION_KEYS not configured")
    return MultiFernet([Fernet(k.encode()) for k in keys])


def reset_crypto_cache() -> None:
    _fernet.cache_clear()


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:  # wrong key or tampered ciphertext
        raise RuntimeError("unable to decrypt stored secret (check ZG_ENCRYPTION_KEYS)") from exc


def rotate_secret(value: str | None) -> str | None:
    """Re-encrypt with the current primary key (first key in ZG_ENCRYPTION_KEYS)."""
    if not value:
        return value
    return _fernet().rotate(value.encode()).decode()


def new_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="ZoneGuard AI")
