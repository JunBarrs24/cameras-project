# Phase 2: productize the edge

Goal: turn the hand-managed pilot edge into a product: our own preconfigured box, remote fleet management, and multi-camera support, so adding a site stops requiring an engineer on a chair.

This plan is written two phases ahead; steps will be refined with Phase 1 pilot learnings. Requirements, outcomes, and validation criteria are the commitment.

## Value delivered

Scale. After this phase, onboarding a paying client means shipping a preconfigured box that self-registers, and supporting it means looking at a fleet dashboard instead of asking the client to restart a PC. This is what makes D-005's production rule ("paid production always on our box") operational, and what drops support cost per site to something a subscription can absorb.

## Input

- Phase 1 complete: cloud live, one pilot finished, onboarding document tested.
- At least one client ready to pay (the trigger for buying hardware).
- Pilot learnings: real per-camera CPU load, event volumes, failure modes observed.

## Required

- 1 or 2 candidate edge devices for benchmarking: Intel N100-class mini-PC and Jetson Orin Nano (per ARCHITECTURE.md hardware section).
- A way to image devices reproducibly (see step 1).

## Steps

### Step 1: edge packaging

- Containerize the edge (Docker image) or define a systemd-managed install; decision proposed to DECISIONS.md when benchmarking says which fits the hardware.
- Reproducible provisioning: a base OS image plus a bootstrap script that takes a site token and brings the box to running state with no keyboard attached.

Files: `edge/Dockerfile` or `edge/deploy/*` (C), provisioning scripts (C)
Validation: wiping and re-provisioning a box takes under 30 minutes and zero interactive steps after the token.

### Step 2: device registry and enrollment

- `cloud/fleet/`: device registry (device id, site, hardware, version, last heartbeat). Enrollment flow: box presents its site token once, receives its API key and config.

Files: `cloud/fleet/*` (C), `edge/agent/enroll.py` (C)
Validation: a factory-fresh box plugged into a network with the NVR appears in the registry and starts streaming events with no manual config on the box.

### Step 3: remote configuration

- The edge pulls its profile, zones, and camera list from the cloud on start and on change (poll or push; decide with real constraints). Zone edits happen in the dashboard, propagate to the box, no SSH involved.

Files: `edge/agent/config_sync.py` (C), `cloud/fleet/` (M), dashboard zone editor (M)
Validation: changing a zone polygon in the dashboard alters edge behavior within minutes, verified by events.

### Step 4: updates (OTA)

- Pull-based updater: the box checks for a signed release, applies it, and rolls back on failed health check. Staged rollout (one canary site first).

Files: `edge/agent/updater.py` (C), release tooling (C)
Validation: a deliberately broken release rolls back automatically on the canary; a good release reaches the fleet.

### Step 5: health and ops monitoring

- Heartbeat from every box (stream status per camera, queue depth, temperature, disk). Fleet dashboard page and an internal alert when a site goes silent (this alert goes to us, the operators, unlike client alerts).

Files: `edge/agent/heartbeat.py` (C), `cloud/fleet/` (M)
Validation: unplugging a box raises an internal alert within 5 minutes; a camera going dark shows per-camera, within one heartbeat cycle.

### Step 6: multi-camera per box and benchmark

- Run N ingest/detect loops on one box; measure streams per device at 5 to 10 fps with yolo11n on both candidate devices; publish the numbers in this repo (they drive hardware choice per site size and the pricing floor).

Files: `edge/app.py` (M), `docs/BENCHMARKS.md` (C)
Validation: documented streams-per-device table; a 4-camera site runs on the chosen low-end box with headroom.

## Phase validation (exit criteria)

1. A new site goes live by shipping a box: enrollment, config, and zones all remote.
2. One full OTA cycle (canary, rollout, and a forced rollback) executed on real hardware.
3. Fleet page shows live health for every deployed box; silent-site alert tested.
4. Benchmarks published; hardware per site size decided and proposed to DECISIONS.md.
5. Support playbook: the three most common failures from the pilot are detectable remotely.

## Out of scope

Construction vertical (Phase 3), billing automation, multi-tenant admin beyond basic site separation.
