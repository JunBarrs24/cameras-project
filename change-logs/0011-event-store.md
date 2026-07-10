# 0011: Event store

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 8. Added the SQLite event store, the local buffer at the edge.

- `edge/events.py`:
  - `EventStore` over stdlib `sqlite3`. The `events` table mirrors the shared
    `Event` schema (the `class` alias is a quoted SQL column) plus an `uploaded`
    flag for the Phase 1 uploader.
  - Opened in WAL mode, because the real edge failure is a power cut on an
    unattended box; WAL keeps the file consistent across an abrupt stop. Each
    write commits, so a stored event is durable before the loop moves on.
  - `add(event, frame=None)`: inserts the event, and when a frame is given (a
    rule with `emit.snapshot`) writes a JPEG into the snapshot directory and
    records its path. The event is immutable, so a copy carries `snapshot_ref`.
  - `get`, `pending` (unuploaded, oldest first), `mark_uploaded`, and `count`.
    `pending`/`mark_uploaded` define the boundary the Phase 1 uploader will use.
  - Rows round-trip back through `Event.model_validate`, so reads are validated
    against the same schema as writes.
- `tests/test_events.py`: insert/read round trip, a missing id returning None,
  a snapshot written to disk and referenced on the event, pending plus
  mark_uploaded, and persistence across reopening the file (WAL durability).

## Why

The store is the head of the offline-tolerant path (ARCHITECTURE.md 2): events
land locally first and sync later, so an internet outage never loses a fact.
Mirroring the shared schema keeps the edge buffer and the cloud system of record
speaking one contract (D-011).

## Files created / modified / deleted

- Created: `edge/events.py`, `tests/test_events.py`,
  `change-logs/0011-event-store.md`.
- Modified: `change-logs/INDEX.md`.
- `.gitignore` already ignores `data/`, which covers both `data/edge.db` and the
  default `data/snapshots/`, so no change was needed there.

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass.
- `uv run ty check`: pass.
- `uv run pytest`: pass (59 passed, 1 skipped: the clip-dependent tracking test).

No suppressions. Snapshot writing is exercised in a test with a synthetic frame,
so the on-disk JPEG path is covered without a camera.

## Decisions, biases, tradeoffs

- Applies D-011 (storage split): embedded SQLite in WAL mode at the edge, the
  shared `Event` schema mirrored, an `uploaded` flag added for the sync.
- No new decision proposed here.
