# ZoneGuard AI

**Your Cameras. Smarter Security. Privacy by Design.**

ZoneGuard AI is a multi-tenant B2B SaaS MVP that connects to existing CCTV, detects people with a real AI
model, watches configured restricted zones and entrance boundaries, and raises *potential* incidents for
human review with email alerts. It is built for schools, offices, clinics, retail and warehouses, and is
designed around Australian privacy expectations.

> **What this is, honestly:** a working pilot MVP. Person detection is real (YOLOX, Apache-2.0, via ONNX
> Runtime). Weapon and face-covering modules are **experimental or simulated and clearly labelled**. No
> accuracy numbers are claimed: none have been measured on representative footage yet. Nothing here is
> legally compliant by default; see [the compliance checklist](docs/COMPLIANCE_CHECKLIST_AU.md). Detections
> are observations, never conclusions about a person.

| | |
|---|---|
| Status, milestones, gaps | [docs/STATUS.md](docs/STATUS.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Security & privacy | [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md) |
| AU compliance checklist (legal review items) | [docs/COMPLIANCE_CHECKLIST_AU.md](docs/COMPLIANCE_CHECKLIST_AU.md) |
| Licensing review | [docs/LICENSING.md](docs/LICENSING.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Pilot readiness | [docs/PILOT_READINESS.md](docs/PILOT_READINESS.md) |
| Detector evaluation | [evaluation/README.md](evaluation/README.md) |

## Repository layout

```
zoneguard/
├── vision/        shared CV package: YOLOX ONNX detector, anonymous tracker, zones, privacy masks,
│                  obstruction heuristic, experimental weapon / face-covering modules
├── backend/       FastAPI + SQLAlchemy + Alembic API, rule engine, incidents, email, retention, tests
├── edge_agent/    on-premises agent: RTSP ingestion, local processing, durable queue, sync, ONVIF discovery
├── frontend/      Next.js 15 + TypeScript + Tailwind dashboard, Vitest + Playwright tests
├── evaluation/    precision/recall/latency evaluation framework
├── models/        model weights (downloaded, not committed)
├── samples/       sample footage (downloaded, not committed)
├── scripts/       download + test helpers
└── docker-compose.yml
```

## Quick start (Docker Compose)

Requires Docker with Compose v2.

```bash
cd zoneguard
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD and ZG_ENCRYPTION_KEYS
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # needs `pip install cryptography`
./scripts/download_models.sh          # YOLOX ONNX weights (Apache-2.0), SHA-256 verified
./scripts/download_samples.sh         # optional: OpenCV pedestrian clip, dev only
docker compose up --build
```

* Dashboard: http://localhost:3000 (register an organisation)
* Test emails: Mailpit at http://localhost:8025
* The API and database are not published to the host; the dashboard proxies `/api`.

### Demo walkthrough (the acceptance workflow)
1. **Register** at `/register` (you become organisation admin).
2. **Settings → Sites** → create a site (pick its time zone).
3. **Cameras → Add camera** → source "Uploaded staged video".
4. **Video Analysis** → upload staged footage (e.g. `samples/vtest.avi`). Set "Recorded at" to an
   evening time, e.g. 22:00, and confirm the consent attestation.
5. **Zones** → pick the camera, click 3+ points to draw the restricted area, name it "Finance Office" and
   keep "Also create an after-hours rule" ticked → **Save zone**.
6. **Video Analysis** → select the video → **Start analysis**. Review bounding boxes and timestamped events; export CSV/JSON.
7. **Incident Centre** → open the potential incident → acknowledge / escalate / dismiss / close. The audit trail records each step.
8. Open Mailpit to see the alert email (no images, by design).
9. Register a second organisation in a private window: it cannot see any of the first organisation's data.

## Local development (without Docker)

Prerequisites: Python 3.11+, Node 22+, PostgreSQL 16.

```bash
cd zoneguard
python3 -m venv .venv && . .venv/bin/activate
pip install -e vision -e edge_agent -r backend/requirements-dev.txt
./scripts/download_models.sh && ./scripts/download_samples.sh

# database
createuser -P zoneguard && createdb -O zoneguard zoneguard

# API
cd backend
cat > .env <<EOF
ZG_DATABASE_URL=postgresql+psycopg://zoneguard:<password>@localhost:5432/zoneguard
ZG_ENCRYPTION_KEYS=<fernet key>
ZG_EMAIL_BACKEND=console          # or smtp with ZG_SMTP_HOST/PORT (e.g. Mailpit on 1025)
ZG_MODEL_DIR=../models
EOF
alembic upgrade head
uvicorn app.asgi:app --reload --port 8000          # API docs: http://localhost:8000/api/docs

# dashboard (new terminal)
cd ../frontend && npm ci && npm run dev             # http://localhost:3000 (proxies /api to :8000;
                                                     # set ZG_BACKEND_URL before `next build` to change)
```

## Testing

| Suite | Command | Notes |
|---|---|---|
| Backend + vision (56 tests) | `cd backend && pytest -q` | SQLite by default; for PostgreSQL: `ZG_TEST_DATABASE_URL=postgresql+psycopg://user:pw@localhost/zoneguard_test pytest -q`. Real-model tests are skipped (not faked) if `models/` or `samples/vtest.avi` are missing. |
| Edge agent (7) | `cd edge_agent && pytest -q tests` | |
| Evaluation metrics (6) | `pytest -q evaluation/tests` (from `zoneguard/`) | |
| Frontend unit (7) | `cd frontend && npm test` | Vitest + Testing Library |
| Frontend types | `cd frontend && npm run lint` | `tsc --noEmit` |
| Browser E2E (acceptance) | start API + dashboard (+ SMTP sink), then `cd frontend && ZG_E2E_MAIL_DIR=<dir> npx playwright test` | Full brief §14 workflow through the UI with real YOLOX detection. `ZG_E2E_BASE_URL` targets another stack. Raise `ZG_RATE_LIMIT_REGISTER_PER_HOUR` on the API if you re-run it often (default 5 registrations/hour/IP). |
| Everything except E2E | `./scripts/run_all_tests.sh` | |

Migrations are checked against the models with `cd backend && alembic check`.

## Edge agent

Runs inside the customer network, so video never leaves it by default. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#edge-agent-customer-site).

```bash
export ZG_EDGE_API_URL=https://zoneguard.example.com.au ZG_EDGE_TOKEN=zge_...   # token from Settings → Edge agents
zoneguard-edge check        # list assigned cameras
zoneguard-edge run          # process streams, sync event metadata, heartbeat
zoneguard-edge discover     # ONVIF WS-Discovery on the LAN
zoneguard-edge snapshot --camera <id>   # one privacy-masked still for zone drawing
```

Local development against `http://localhost:8000` requires `ZG_EDGE_ALLOW_INSECURE_HTTP=true`.
With Compose: `ZG_EDGE_TOKEN=zge_... docker compose --profile edge up edge`.

## Operations CLI

```bash
cd backend
python -m app.cli rotate-keys       # after prepending a new key to ZG_ENCRYPTION_KEYS
python -m app.cli retention-sweep   # run deletion sweep now (also runs hourly)
```

## Things that need external credentials, hardware, data or approval

See the table at the end of [docs/STATUS.md](docs/STATUS.md). In short: real cameras or an RTSP server for
live testing, edge hardware, consented staged footage with annotations, licensed specialist models, an SMTP
provider, TLS and hosting, legal review, and customer approval before monitoring any real site.
