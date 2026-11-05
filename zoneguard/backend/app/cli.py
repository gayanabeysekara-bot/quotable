"""Operational CLI.

  python -m app.cli rotate-keys      re-encrypt stored secrets with the first key in ZG_ENCRYPTION_KEYS
  python -m app.cli retention-sweep  run the retention/deletion sweep for all organisations now
"""

from __future__ import annotations

import sys

from sqlalchemy import select


def rotate_keys() -> int:
    from .db import session_factory
    from .models import Camera, User
    from .security import rotate_secret

    db = session_factory()()
    n = 0
    try:
        for cam in db.scalars(select(Camera)).all():
            for field in ("username_enc", "password_enc"):
                v = getattr(cam, field)
                if v:
                    setattr(cam, field, rotate_secret(v))
                    n += 1
        for u in db.scalars(select(User).where(User.mfa_secret_enc.is_not(None))).all():
            u.mfa_secret_enc = rotate_secret(u.mfa_secret_enc)
            n += 1
        from . import audit

        audit.record(db, "security.keys_rotated", actor_type="system", actor_label="cli", details={"values": n})
        db.commit()
    finally:
        db.close()
    print(f"re-encrypted {n} stored secrets with the primary key")
    return 0


def retention_sweep() -> int:
    from .db import session_factory
    from .services.retention import sweep_all

    db = session_factory()()
    try:
        print(sweep_all(db))
    finally:
        db.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmds = {"rotate-keys": rotate_keys, "retention-sweep": retention_sweep}
    if not args or args[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[args[0]]()


if __name__ == "__main__":
    sys.exit(main())
