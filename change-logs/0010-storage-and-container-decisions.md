# 0010: Storage and container decisions

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

No code. Records two decisions the developer validated in conversation, before
step 8 builds the edge event store on the first of them.

- D-011: storage split. Edge stores events in embedded SQLite (stdlib `sqlite3`,
  single file, WAL mode); cloud stores them in Postgres. The `shared/` `Event`
  schema is the one contract both mirror; the edge table adds an `uploaded` flag.
- D-012: container strategy. Cloud in Docker from Phase 1; edge native (uv) in
  Phase 0 and pilots, containerized in Phase 2 when the box is productized, for
  OTA updates, atomic rollback, and fleet consistency.

## Why

The question came up ahead of step 8 (event store): why SQLite and not Postgres,
and whether everything ships in Docker. Both were implied by D-001 (hybrid edge
plus cloud) and D-005 (production on our unattended box) but never stated, so
they are recorded explicitly to anchor step 8 and the Phase 1 and Phase 2 plans.

The reasoning, in short: the edge is an unattended appliance store staff
power-cycle, so it wants the fewest moving parts. SQLite is a library, not a
server (no daemon, port, roles, or backups), and its single-writer, low-volume
write pattern needs nothing Postgres offers. The cloud is multi-tenant with
concurrent readers and writers, where Postgres fits. Containers earn their cost
on the edge only in Phase 2, when fleet OTA and rollback outweigh the
hardware-passthrough friction (iGPU/OpenVINO or Jetson, video devices, RTSP).

## Files created / modified / deleted

- Created: `change-logs/0010-storage-and-container-decisions.md`.
- Modified: `docs/DECISIONS.md` (append D-011 and D-012),
  `change-logs/INDEX.md`.

## Validation

No code, no validators to run. The markdown passes the em-dash guard.

## Decisions, biases, tradeoffs

- Records D-011 and D-012 as validated, following the governance flow (propose in
  a change log, then append to DECISIONS.md on explicit validation by the
  developer). Both build on D-001 and D-005.
