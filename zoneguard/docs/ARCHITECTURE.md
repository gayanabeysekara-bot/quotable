# ZoneGuard AI — Architecture

## Components

```
 Customer network (edge)                                   ZoneGuard cloud (SaaS)
 ┌──────────────────────────────────────┐                 ┌──────────────────────────────────────────┐
 │ IP cameras / NVR ──RTSP (read-only)──┐│                 │  Next.js dashboard  (same-origin proxy)  │
 │                                     ▼│                 │        │  /api/* rewrite                 │
 │ zoneguard-edge (Docker)              │   HTTPS,        │        ▼                                 │
 │  ├─ CameraWorker per camera          │   bearer token  │  FastAPI API ──── PostgreSQL             │
 │  │   OpenCV/FFmpeg → privacy masks   │   event         │   ├─ auth / RBAC / tenant isolation      │
 │  │   → YOLOX (ONNX Runtime, CPU)     │   METADATA ────▶│   ├─ rule engine → incidents             │
 │  │   → anonymous IoU tracker         │   only          │   ├─ notification dispatcher → SMTP      │
 │  │   → zone / line crossing          │                 │   ├─ upload analysis worker (same CV     │
 │  │   → specialist modules (opt-in)   │◀── config ──────│   │   pipeline, for staged footage)      │
 │  ├─ durable SQLite event queue       │   (cameras,     │   ├─ retention sweeper, camera-health    │
 │  └─ sync + heartbeat + reconnect     │   zones, creds) │   └─ audit log                           │
 └──────────────────────────────────────┘                 └──────────────────────────────────────────┘
```

* **`vision/` (`zoneguard_vision`)** – shared CV package used by both the cloud upload analyser and the
  edge agent, so staged-footage results reflect what the edge will do on live streams.
  * `detectors/yolox_onnx.py` – YOLOX (Apache-2.0) via ONNX Runtime; letterbox, grid decode, NMS; SHA-256
    verification of official weights.
  * `tracker.py` – greedy IoU tracker. Integer IDs, per camera, per session, expire after a few missed
    frames. No appearance embeddings, so no re-identification is possible.
  * `zones.py` – polygon entry (bottom-centre "feet" anchor) and directed line crossing (sign change of the
    anchor relative to the boundary, robust to anchors landing exactly on the line, extent-checked).
  * `privacy.py` – masks applied **before** detection, previews and snapshots.
  * `obstruction.py` – heuristic (not ML) dark / washed-out / featureless frame detector.
  * `detectors/weapon.py`, `detectors/face_covering.py` – experimental / simulated modules with explicit
    labelling (see STATUS.md).
* **`backend/`** – FastAPI + SQLAlchemy 2 + Alembic. `app/services/rule_engine.py` is the single place
  where events become incidents.
* **`edge_agent/`** – Python service (`zoneguard-edge run|check|discover|snapshot`).
* **`frontend/`** – Next.js 15 App Router, TypeScript, Tailwind, shadcn-style components.

## Data hierarchy (multi-tenant)

`Organisation → Site → Camera → Zone → Rule → Event → Incident` (+ IncidentHistory, Notification).
Every tenant-owned table has `org_id`. All org-scoped routes live under `/api/orgs/{org_id}/…`;
`deps.get_org_context` verifies membership on **every** request and returns 404 (not 403) for
non-members so other tenants' existence is not disclosed. Child objects are fetched with
`get_owned(model, id, org_id)`, which 404s on any cross-tenant ID. Edge agents are bound to one
org **and** one site; events for cameras/zones outside that scope are rejected.

## Event → incident pipeline

```
detection (frame) → tracker → zone/line event ─┐
weapon / face-covering module (opt-in) ────────┼─▶ Event row (model name+version+status, simulated flag)
camera offline / obstruction ──────────────────┘          │
                                                           ▼
                         rule_engine.evaluate_event()
   org feature gate → zone enabled & within monitoring hours → NOT within approved access period
   → each matching enabled rule (scope: site/camera/zone; min confidence; active schedule in site tz)
   → suppression window (fold into open incident, increment counter) OR create Incident
   → IncidentHistory "created" + Notification rows (queued) ──▶ dispatcher → EmailChannel (SMTP)
                                                           ▼
            Human review: acknowledge / escalate / dismiss(reason) / close(reason) / reopen
            every transition → IncidentHistory + AuditLog
```

Severity is capped per category (`face_covering_observed` ≤ informational). No code path performs
automatic external actions (no emergency calls, door locks, access-control changes).

## Edge ↔ cloud protocol

| Endpoint (bearer `zge_…`) | Purpose |
|---|---|
| `GET /api/edge/config` | Cameras for this agent's site (credentials decrypted for the agent only), zones, masks, org feature flags |
| `POST /api/edge/events` | Batch (≤500) of event metadata; idempotent via `agent_id:idempotency_key` unique constraint |
| `POST /api/edge/heartbeat` | Agent CPU/RAM/queue depth + per-camera status, fps, reconnect counters; status transitions to `offline` raise `camera_offline` events |
| `POST /api/edge/discovery` | ONVIF WS-Discovery results for the admin UI |
| `POST /api/edge/cameras/{id}/snapshot` | One admin-requested, privacy-masked still for zone drawing (re-encoded server-side) |

Offline behaviour: events are written to a local SQLite (WAL) queue first, then synced in order;
failures back off exponentially (max 60 s). The queue is bounded (oldest dropped and counted).
Camera reads use exponential backoff with jitter (1 s → 60 s). The cloud also marks cameras
offline when no heartbeat arrives for 120 s.

## Upload analysis

`POST /videos` streams to disk with a size cap and magic-byte check, then `probe_video` decodes it
with resolution/duration limits. `POST /videos/{id}/analyses` queues a job on a bounded thread pool
(`services/dispatch.py`). The worker samples frames (default 5 fps), stores per-frame detections
(`frame_detections`, for bounding-box review), creates events timestamped at
`recorded_at + offset`, evaluates rules, and records stats (frames, p95 inference ms, CPU %, peak RSS).

## Scaling notes (beyond pilot)

* Replace the in-process thread pool with a durable queue (e.g. a Postgres-backed job table or Redis)
  and run analysis workers separately; the worker function is already stateless (`run_job(job_id)`).
* Replace the in-memory rate limiter with a shared store.
* Object storage (S3-compatible, server-side encryption) for uploads; storage access is isolated
  in `services/storage.py`.
* GPU / OpenVINO execution providers can be added in `YoloxOnnxDetector` without API changes.
