# Phase 1: cloud side and first pilot (tienda)

Goal: stand up the minimal cloud (event ingestion API, Postgres, snapshot storage, alerts, dashboard), connect the Phase 0 edge to it, and run a real pilot in one store on hardware the store already has (per D-005).

This plan is written before Phase 0 is finished, so step details will be refined when the phase starts; the requirements, outcomes, and validation criteria below are the commitment.

## Value delivered

The first complete product loop: something happens in the store, the owner receives an alert on their phone and sees it in a dashboard. This is the demo that sells, and the pilot produces the first external feedback and the first reference customer.

## Input

- Phase 0 complete: edge pipeline producing events into local SQLite with an `uploaded` flag.
- A pilot store agreed (owner willing, NVR with RTSP access, a capable PC or spare machine on premises).
- A small VPS (Hetzner or DigitalOcean class; 2 to 4 GB RAM is enough at this scale).
- Telegram bot token for alerts (per D-008, proposed).

## Required

- Docker and docker compose on the VPS.
- A domain or subdomain with TLS (Caddy or Traefik handles certificates).
- Site onboarding data: camera list, RTSP credentials, drawn zones, alert recipients.

## Steps

### Step 1: cloud skeleton

- `cloud/api/`: FastAPI app with `POST /v1/events` (batch) and `POST /v1/snapshots`, authenticated by a per-site API key; `GET /health`.
- `cloud/db/`: Postgres schema mirroring `shared/schemas.py` (the API validates with the same pydantic models, keeping one source of truth). Migrations with alembic.
- Snapshot storage: local disk volume first; S3-compatible object storage when more than one site is live.
- `docker-compose.yml` for api + postgres + reverse proxy.

Files: `cloud/api/*` (C), `cloud/db/*` (C), `docker-compose.yml` (C), `shared/` (M if auth fields are needed)
Validation: compose up locally; posting a fixture event batch returns 200 and lands in Postgres; a wrong API key returns 401.

### Step 2: edge uploader

- `edge/uploader.py`: reads unuploaded events from SQLite, posts in batches with retry and exponential backoff, marks them uploaded. Snapshots upload the same way.
- Offline behavior is the point: the edge keeps recording events with no internet and drains the queue on reconnect.

Files: `edge/uploader.py` (C), `edge/app.py` (M), `tests/test_uploader.py` (C, against a fake server)
Validation: unit tests for retry and marking; manual test cutting internet for 10 minutes and watching the queue drain afterward.

### Step 3: alerts

- `cloud/alerts/`: worker that consumes high-severity events and sends Telegram messages (photo plus text: site, camera, zone, rule, time) to the site's configured recipients. Rate limiting per rule so one incident does not flood a phone.

Files: `cloud/alerts/*` (C), `tests/test_alerts.py` (C)
Validation: a staged intrusion event produces exactly one Telegram message within 30 seconds, snapshot attached.

### Step 4: minimal dashboard

- `cloud/dashboard/`: server-rendered pages (FastAPI plus templates; a JS framework is not justified at this size): login per site, event list with snapshot preview and filters (camera, zone, type, date), traffic-by-hour chart, and a zone table with visit counts and average dwell.

Files: `cloud/dashboard/*` (C)
Validation: the pilot owner can log in from a phone and answer "what happened yesterday" without help.

### Step 5: deploy and onboarding kit

- Deploy the compose stack to the VPS with TLS.
- `docs/ONBOARDING.md`: checklist to bring a site live (NVR access, RTSP URLs per camera, zone drawing session, alert recipients, API key issuance, videovigilancia signage reminder aligned with D-004).
- Retention enforcement: a scheduled job deletes snapshots past 30 days and applies the other D-004 defaults.

Files: `docs/ONBOARDING.md` (C), deploy config (C), retention job (C)
Validation: a second fake "site" onboards end to end in under one hour following only the document; retention job verifiably deletes expired snapshots.

### Step 6: the pilot itself

- Install the edge on the store's machine (D-005), configure cameras and zones, run 2 to 4 weeks.
- Weekly review with the owner: which alerts were useful, which were noise, what is missing. Adjustments go in as profile/config changes (D-003 discipline).

## Phase validation (exit criteria)

1. An event generated in the store reaches the dashboard in under 60 seconds end to end.
2. A staged after-hours zone entry triggers a Telegram alert with snapshot in under 30 seconds.
3. A forced 10-minute internet outage at the store loses zero events.
4. The pilot runs 2 consecutive weeks without manual intervention on the edge machine.
5. The owner states, unprompted, that at least one alert or report is worth paying for. If the answer is still no after 4 weeks, that finding is proposed to DECISIONS.md as input for repositioning.

## Out of scope

Fleet management, remote updates, multi-site dashboards, WhatsApp, billing, our own edge hardware. Those belong to Phase 2.
