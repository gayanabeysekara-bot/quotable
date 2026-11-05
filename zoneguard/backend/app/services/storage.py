"""Local media storage. Files are stored under random names outside any web root and are only
served through authenticated, tenant-scoped endpoints."""

from __future__ import annotations

import secrets
from pathlib import Path

from ..config import get_settings


def root() -> Path:
    p = Path(get_settings().storage_dir).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def new_key(org_id, ext: str) -> str:
    return f"{org_id}/{secrets.token_hex(16)}{ext}"


def path_for(key: str) -> Path:
    base = root()
    p = (base / key).resolve()
    if base not in p.parents:  # path traversal guard
        raise ValueError("invalid storage key")
    return p


def delete(key: str | None) -> bool:
    if not key:
        return False
    p = path_for(key)
    if p.exists():
        p.unlink()
        return True
    return False
