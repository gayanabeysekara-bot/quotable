# Implementation Status

Status as of this MVP build. "Verified" means exercised by an automated test or an end-to-end run in
the development environment, as noted. Nothing here claims real-world detection accuracy.

## Milestones

| Milestone | Status | Evidence |
|---|---|---|
| 1 — Foundation: repo, DB, auth, multi-tenant models, dashboard, upload analysis, real person detection, basic zones | **Complete** | Alembic migration on PostgreSQL 16; `test_auth_security`, `test_tenancy_rbac`, `test_uploads`, `test_real_detection` (YOLOX on real pedestrian footage) |
| 2 — Detection & events: zone crossing, schedules, events, incident persistence & review workflow, experimental interfaces | **Complete** | `test_acceptance_workflow`, `test_vision`, `test_schedules_rules` |
| 3 — Live cameras: RTSP ingestion, registration, local edge processing, health, sync, reconnect | **Complete, one gap** | `test_edge_integration` (agent → API with local stream, idempotent sync, offline incidents), `test_edge_agent` (reconnect/backoff, outage buffering). **Gap:** a successful read from a real RTSP server/camera was not verified in this sandbox (running a downloaded RTSP server binary was not permitted). Against an unreachable RTSP URL, real connection attempts, backoff, reconnect counters and `camera_offline` alerting were all verified. |
| 4 — Alerts & security: email, suppression, access control, audit, retention, hardening | **Complete** | SMTP delivery to a real local SMTP server (`test_real_smtp_delivery`; Mailpit in the Docker stack), suppression test, RBAC/isolation tests, retention + key-rotation tests |
| 5 — Pilot validation: tests, synthetic data, evaluations, docs, deployment guide, pilot checklist | **Framework complete; validation pending** | Evaluation framework + tests; latency/resource report on sample footage. **No precision/recall has been measured**: that needs annotated, consented staged footage (see evaluation/README.md). |

### Acceptance criteria (brief §14)

All 12 steps are automated twice: at API level (`backend/tests/test_acceptance_workflow.py`, with a
labelled test-double detector for determinism) and through the real browser UI with **real YOLOX
detection** (`frontend/tests/e2e/acceptance.spec.ts`). Both passed against (a) a local
PostgreSQL + uvicorn + Next.js stack with a local SMTP sink and (b) the Docker Compose stack with Mailpit.

## Feature status

### Completed (working)
* Organisation registration, login/logout, Argon2id passwords, server-side sessions, optional TOTP MFA, password change, lockout and rate limits.
* Roles: org admin, site manager, security reviewer, read-only auditor (server-enforced); invitations (single-use, 7-day expiry); member role changes with last-admin protection.
* Strict org-level isolation (404 on cross-tenant access), edge agents bound to org + site.
* Sites with time zones; cameras (upload / RTSP / ONVIF-addressed) with encrypted write-only credentials, edge assignment, privacy masks, health/status.
* Staged video upload with layered validation; annotated-frame rendering; authenticated streaming; CSV/JSON metadata export.
* Genuine person detection (YOLOX nano/tiny/s via ONNX Runtime), anonymous short-lived tracking, bounding boxes, confidence scores, model name/version on every event and incident.
* Zone drawing UI (polygons + directed entrance lines), monitoring hours, approved-access periods, a quick after-hours rule.
* Rule engine: categories, scope, schedules in site timezone (incl. overnight), min confidence, severity (4 levels, face-covering capped), suppression windows.
* Incident Centre: queue, filters, detail, assign, notes, acknowledge/escalate/dismiss (reason)/close (reason)/reopen, full history + audit.
* Email notifications (SMTP), no imagery, delivery status and latency recorded; push/SMS interfaces defined.
* Edge agent: RTSP/HTTP/file sources via OpenCV/FFmpeg, per-camera workers, reconnect with exponential backoff + jitter, local durable queue, idempotent batch sync, heartbeats, ONVIF WS-Discovery, admin-triggered masked snapshot, HTTPS enforcement.
* Camera offline detection (edge-reported + cloud heartbeat timeout) and heuristic obstruction detection.
* Retention & deletion (per-org periods, hourly sweep, manual run, audited); key rotation CLI.
* Dashboard pages A–G plus an evaluation page; responsive (mobile card layout for incidents), dark navy/teal theme.
* Docker images for API, dashboard and edge agent; Compose stack (Postgres, Mailpit) verified.

### Experimental (clearly labelled in UI, API, emails)
* **Weapon module.** `simulated_test` = labelled fake detections for workflow testing. `coco_knife_unvalidated` = generic COCO "knife" class: not a weapon detector, no firearm class, never validated. `onnx_custom` interface for a properly licensed, validated model (none bundled). Off by default per org.
* **Face-covering module.** `simulated_test` only, plus an `onnx_classifier` interface with a label allow-list. No model bundled. Off by default; neutral, capped at Informational.
* **Obstruction detection.** Heuristic (brightness/variance/edges), not ML; needs per-site tuning.

### Incomplete / not implemented
* ONVIF **GetStreamUri / PTZ / profile** calls: discovery lists devices; RTSP URLs are entered manually.
* Access-control (badge system) integration: future interface only, documented.
* Push and SMS channels: interface classes raise `NotImplementedError`.
* Formal data-subject access request workflow; per-site scoping of site-manager role (roles are org-wide).
* WebAuthn / enforced MFA policy; SSO (SAML/OIDC).
* Billing / subscription management (data model has a `plan` field only).
* Durable job queue and shared rate-limit store for horizontal scaling.
* Measured precision/recall on representative footage; independent validation; penetration test.

## Requires external input

| Need | Why | Who |
|---|---|---|
| Real IP cameras / NVR on a test network (or an RTSP server) | Verify live RTSP read, camera-specific URL formats, long-run reconnect behaviour | Customer IT / pilot team |
| Edge hardware (x86 mini-PC, 4+ cores; optional GPU/NPU) | Latency/CPU budgeting per camera | Pilot team |
| Staged, consented footage covering the scenario list + ground-truth annotations | Precision/recall, false alerts, bias checks | Pilot team, with participant consent forms |
| A licensed, trained weapon model (and its validation report) | Replace experimental modes | Vendor / ML team + legal |
| A licensed face-covering classifier (optional) | Same | Vendor / ML team + legal |
| SMTP provider credentials (e.g. Amazon SES, Postmark) and a sending domain with SPF/DKIM | Production email | Ops |
| TLS certificates, domain, hosting in an Australian region, secret manager | Production deployment | Ops |
| Legal review (privacy, workplace surveillance, schools, licences) | See COMPLIANCE_CHECKLIST_AU.md and LICENSING.md | Counsel |
| Human approval before monitoring any real site, especially schools | Policy and consent | Customer leadership |
