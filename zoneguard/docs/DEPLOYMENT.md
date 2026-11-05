# Deployment Guide (pilot)

The Docker Compose file is for **local development**. A pilot deployment needs the following.

## Cloud (dashboard + API + database)

1. **Hosting** in an Australian region. Run `zoneguard-api` and `zoneguard-web` containers behind a
   TLS-terminating reverse proxy / load balancer. Only the dashboard origin is public; the API is reached
   through the dashboard's `/api` proxy (or route `/api/*` at the proxy to the API service on the private
   network). Never expose PostgreSQL publicly.
2. **Database:** managed PostgreSQL 16 with encryption at rest, automated backups, TLS
   (`?sslmode=require` in `ZG_DATABASE_URL`). Migrations run on API start (`alembic upgrade head`).
3. **Secrets** from a secret manager, injected as environment variables:
   `ZG_ENCRYPTION_KEYS`, `ZG_DATABASE_URL`, `ZG_SMTP_PASSWORD`. Never bake them into images.
4. **Required production settings:**
   ```
   ZG_ENVIRONMENT=production      # disables API docs; enforces the checks below
   ZG_COOKIE_SECURE=true          # HTTPS-only cookies, HSTS
   ZG_EMAIL_BACKEND=smtp          # console/memory refused in production
   ZG_PUBLIC_BASE_URL=https://zoneguard.example.com.au
   ZG_TRUSTED_PROXY_COUNT=1       # see "Client IPs" below
   ```
   **Client IPs (rate limiting & audit):** the Next.js `/api` proxy forwards `X-Forwarded-For` unchanged
   and does not append the caller's address. Put a reverse proxy / load balancer that **appends** the
   client IP (AWS ALB, nginx `proxy_add_x_forwarded_for`) in front of the dashboard and set
   `ZG_TRUSTED_PROXY_COUNT=1`. Without such a proxy keep it at `0`, but then every browser request appears
   to come from the dashboard container, so per-IP limits are shared by all users (per-account login
   limits still apply). Verified behaviour: with count `1` the API records the address appended by the
   front proxy; a client-supplied header is only trusted when nothing appends after it.
   **Backend URL:** `ZG_BACKEND_URL` is baked into the dashboard **at build time** (Next.js rewrites are
   compiled into the routes manifest). Pass it as a build argument (as `docker-compose.yml` does).
5. **Storage:** mount a persistent, encrypted volume at `/data/uploads` (or adapt
   `services/storage.py` to S3-compatible storage with SSE). Raw uploads are deleted per retention policy.
6. **Models:** run `scripts/download_models.sh` and mount `models/` read-only at `/models`.
7. **Email:** SMTP provider with SPF/DKIM/DMARC on the sending domain (`ZG_SMTP_*`, `ZG_EMAIL_FROM`).
8. **Single API instance** for the pilot (in-process rate limiter and worker pool). For more, see
   ARCHITECTURE.md → Scaling notes.
9. **Monitoring:** ship the JSON logs to your log platform; alert on `/api/health`, 5xx rates,
   failed notifications (`notifications.status='failed'`) and edge agents not seen for > 5 minutes.

## Edge agent (customer site)

1. Hardware: x86-64 mini-PC, 4+ cores, 8 GB RAM, SSD; wired to the camera VLAN. Rough guide from this
   build's measurements: `yolox_tiny` ≈ 22 ms/frame on 4 vCPUs at 768×576, so ~5 fps × several cameras
   is feasible; measure on your own hardware with `python -m evaluation.run`.
2. Create a **read-only (view-only) user** on each camera/NVR.
3. In the dashboard: Settings → Edge agents → create token (shown once). Cameras → add RTSP camera
   with the credentials and assign the agent.
4. On the device:
   ```bash
   docker run -d --restart unless-stopped --name zoneguard-edge \
     -e ZG_EDGE_API_URL=https://zoneguard.example.com.au \
     -e ZG_EDGE_TOKEN=zge_xxx \
     -v /opt/zoneguard/models:/models:ro -v zoneguard-edge:/data \
     zoneguard-edge:<version>
   docker exec zoneguard-edge zoneguard-edge check           # verify connectivity
   docker run --rm --network host zoneguard-edge:<version> discover   # optional ONVIF discovery (LAN)
   docker exec zoneguard-edge zoneguard-edge snapshot --camera <camera-id>   # one masked still for zone drawing
   ```
5. Firewall: outbound HTTPS (443) to the ZoneGuard API only. No inbound ports are needed. Keep the agent
   on a network segment that can reach cameras but not the internet beyond the API.
6. If the edge must trust a private CA, set `ZG_EDGE_CA_BUNDLE=/path/ca.pem`.

## Operations

* Rotate encryption keys: prepend a new key to `ZG_ENCRYPTION_KEYS`, restart, `python -m app.cli rotate-keys`, remove the old key, restart.
* Rotate or revoke edge tokens in Settings → Edge agents.
* Run retention immediately: `python -m app.cli retention-sweep` (also hourly automatically).
* Backups: database (PITR) and the uploads volume; test restores.
