from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

_tmp = Path(tempfile.mkdtemp(prefix="zg-test-"))
os.environ.setdefault("ZG_ENVIRONMENT", "test")
os.environ["ZG_DATABASE_URL"] = os.environ.get("ZG_TEST_DATABASE_URL", f"sqlite:///{_tmp / 'test.db'}")
os.environ["ZG_ENCRYPTION_KEYS"] = Fernet.generate_key().decode()
os.environ["ZG_EMAIL_BACKEND"] = "memory"
os.environ["ZG_STORAGE_DIR"] = str(_tmp / "uploads")
os.environ.setdefault("ZG_MODEL_DIR", str(Path(__file__).resolve().parents[2] / "models"))
os.environ["ZG_RUN_BACKGROUND_TASKS"] = "false"
os.environ["ZG_RATE_LIMIT_DEFAULT_PER_MINUTE"] = "100000"
os.environ["ZG_RATE_LIMIT_LOGIN_PER_MINUTE"] = "1000"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import models  # noqa: E402,F401
from app.db import Base, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.ratelimit import limiter  # noqa: E402
from app.services import detectors  # noqa: E402
from app.services.notifications import memory_outbox  # noqa: E402

PASSWORD = "Correct-Horse-42!"


@pytest.fixture(scope="session")
def app():
    application = create_app()
    eng = get_engine()
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    return application


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    eng = get_engine()
    with eng.begin() as conn:
        if eng.dialect.name == "postgresql":
            names = ", ".join(t.name for t in Base.metadata.sorted_tables)
            conn.execute(text(f"TRUNCATE {names} CASCADE"))
        else:
            for t in reversed(Base.metadata.sorted_tables):
                conn.execute(t.delete())
    memory_outbox.clear()
    limiter.reset()
    detectors.person_detector_factory = None


class Api:
    """Thin helper adding the CSRF header and org prefix."""

    def __init__(self, client: TestClient):
        self.c = client
        self.org_id: str | None = None

    def _h(self, extra=None):
        h = {"X-Requested-With": "zoneguard"}
        h.update(extra or {})
        return h

    def get(self, path, **kw):
        return self.c.get(self._p(path), **kw)

    def post(self, path, **kw):
        kw["headers"] = self._h(kw.get("headers"))
        return self.c.post(self._p(path), **kw)

    def patch(self, path, **kw):
        kw["headers"] = self._h(kw.get("headers"))
        return self.c.patch(self._p(path), **kw)

    def delete(self, path, **kw):
        kw["headers"] = self._h(kw.get("headers"))
        return self.c.delete(self._p(path), **kw)

    def _p(self, path: str) -> str:
        if path.startswith("org:"):
            return f"/api/orgs/{self.org_id}{path[4:]}"
        return path


def register(client: TestClient, email: str, org: str = "Acme Pilot School") -> Api:
    api = Api(client)
    r = api.post("/api/auth/register", json={"email": email, "password": PASSWORD, "full_name": "Test User",
                                             "organisation_name": org})
    assert r.status_code == 201, r.text
    api.org_id = r.json()["memberships"][0]["org_id"]
    return api


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin(app) -> Api:
    with TestClient(app) as c:
        yield register(c, "admin@acme.example.com")


@pytest.fixture
def make_client(app):
    clients = []

    def _make():
        c = TestClient(app)
        c.__enter__()
        clients.append(c)
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)
