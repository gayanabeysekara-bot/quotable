# Security & Privacy Design

This document describes what is implemented. It is not a certification. See
`COMPLIANCE_CHECKLIST_AU.md` for legal matters that need professional review.

## Privacy by design — fixed safeguards

| Safeguard | Implementation |
|---|---|
| No facial recognition / biometrics | No face detector, embedding or identity model exists in the codebase. The face-covering module only accepts labels from an allow-list (`no_covering, medical_mask, full_face_covering, balaclava, unknown`) and rejects anything else (test: `test_face_covering_classifier_rejects_demographic_labels`). |
| No persistent identity / cross-camera tracking | Tracker IDs are small integers, per camera, per process, expiring after missed frames; no appearance features are computed. |
| No demographic inference | No such model or field exists. |
| Video stays local by default | Edge agent sends only event metadata. The only image an edge agent can send is an admin-triggered privacy-masked still (`zoneguard-edge snapshot`). |
| No external AI APIs | All inference runs locally with ONNX Runtime. There is no code that sends media to third parties. |
| Privacy masks | Applied before detection, preview, snapshot and annotated-frame rendering. |
| Alert emails without imagery | `compose_incident_email` includes text metadata and an authenticated dashboard link only. |
| Neutral language | Incident titles say "Person detected entering …" / "Possible … observed"; every incident page and email carries a disclaimer that detections are not conclusions. |
| Face covering is neutral | Rules for `face_covering_observed` are capped at *Informational* at creation, update and evaluation time; a covering never modifies another incident's severity. |
| Weapon outputs are "possible" | Labelled "possible …"; simulated outputs are prefixed `SIMULATED` and flagged `simulated=true` end-to-end (event, incident, email, UI). |
| Human in the loop | No automatic emergency calls, lockdowns or access-control actions exist. |
| Opt-in specialist modules | Weapon and face-covering modules default to `disabled` per organisation; the API refuses analysis with them unless an org admin enables them; the rule engine drops such events when disabled. |
| Retention | Per-org periods for raw video (default 7 d, max 90 d), frame detections, events, closed incidents and audit logs; hourly sweep + manual run; deletion is audited. |
| Consent attestation | Uploads require an explicit attestation that footage is staged or lawfully obtained. |
| Surveillance notice record | Org admins confirm notice arrangements; timestamp and user are stored and audited; dashboard warns until confirmed. |

## Application security

| Area | Implementation |
|---|---|
| Passwords | Argon2id (`argon2-cffi`), automatic rehash on login, min 12 chars with mixed case + digit, constant-time dummy verification for unknown users. |
| Sessions | Opaque 256-bit random tokens; only SHA-256 stored; `HttpOnly; SameSite=Strict; Secure` (Secure required in production); absolute TTL (12 h) + idle timeout (2 h); server-side revocation on logout and on password change (other sessions). |
| CSRF | SameSite=Strict cookie **and** mandatory `X-Requested-With: zoneguard` header on unsafe methods (cross-site forms cannot set it; no CORS is granted). |
| MFA | TOTP (RFC 6238) enrol/verify/disable; secret encrypted at rest; login with MFA creates an `mfa_pending` session that cannot access any resource until verified. |
| Brute force | Per-IP and per-account login rate limits; account lockout after 8 failures for 15 min; registration, invite acceptance, MFA and upload rate limits; global per-IP limit. |
| Authorisation | Server-side RBAC (`permissions.py`) on every route; tenant isolation via `get_org_context` + `get_owned`; last-admin protection; alert recipients and assignees must be org members. |
| Camera credentials | Fernet (AES-128-CBC + HMAC-SHA256) with `MultiFernet` key rotation (`ZG_ENCRYPTION_KEYS`, first key encrypts); never returned by any user-facing endpoint, never logged (audit details are scrubbed), URLs containing userinfo are rejected; delivered only to the authenticated edge agent of the same site; the edge never writes them to disk. |
| Edge authentication | Per-agent `zge_` bearer tokens, SHA-256 hashed at rest, shown once, rotatable, revocable. Edge refuses plain HTTP except to localhost in explicit dev mode. |
| Upload hardening | Streamed size limit; extension allow-list; magic-byte container sniffing and extension/content match; full decode probe with resolution/duration caps; random storage names outside any web root; files deleted on validation failure; downloads only via authenticated tenant-scoped routes with `no-store`. CSV exports neutralise formula injection. |
| Snapshot hardening | Size cap; decoded and **re-encoded** server-side (strips metadata / polyglot payloads). |
| XML (ONVIF) | Responses with DOCTYPE/ENTITY are rejected; size-capped. |
| Headers | CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, HSTS when secure cookies are on, `no-store` on API responses. API docs disabled in production. |
| Logging | Structured JSON request logs with request IDs; audit log for security-relevant actions (logins, failures, role changes, camera/zone/rule changes, uploads, exports, incident transitions, retention sweeps, edge config fetches). |
| Secrets | No secrets in code; `.env.example` only; production start-up refuses missing encryption keys, insecure cookies, or console email. |
| Network exposure | Compose binds the dashboard and Mailpit to 127.0.0.1; Postgres and the API are not published. |

## Secret rotation

* **Encryption keys:** prepend a new Fernet key to `ZG_ENCRYPTION_KEYS`, restart, run
  `python -m app.cli rotate-keys` to re-encrypt camera credentials and MFA secrets, then remove the old key. Covered by `test_encryption_key_rotation`.
* **Edge tokens:** Settings → Edge agents → rotate/revoke (`POST /edge-agents/{id}/rotate-token`).
* **SMTP credentials / DB password:** environment variables; rotate in your secret manager and restart.

## Known limitations (security)

* Rate limiting is in-process (single instance). Use a shared store when scaling out.
* No WebAuthn yet; TOTP only. MFA is optional (recommend enforcing for admins via policy).
* No malware scanning of uploads beyond container validation and decoding; decoding uses FFmpeg via
  OpenCV — keep images patched, and run the API with least privilege (the Docker image runs as UID 10001).
* Edge ↔ cloud uses bearer tokens over TLS; mutual TLS / device attestation is a recommended hardening.
* An independent penetration test has **not** been performed.
