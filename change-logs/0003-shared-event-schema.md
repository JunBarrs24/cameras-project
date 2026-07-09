# 0003: Shared event schema

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 2. Added the `Event` schema, the contract between edge and cloud,
defined once and used unchanged on both sides.

- `shared/__init__.py`: package marker with a one-line purpose.
- `shared/schemas.py`: the `Event` pydantic model with the exact fields of
  ARCHITECTURE.md section 4 (id, site_id, camera_id, ts, type, severity,
  track_id, zone, class, dwell_s, snapshot_ref, profile_rule_id), plus a
  `Severity` StrEnum (info, low, medium, high, critical). Two design points:
  - `class` is a Python keyword, so the field is `class_name` with the `class`
    alias. The wire format stays faithful to the schema (`model_dump(by_alias=True)`
    emits `class`), and `populate_by_name=True` lets both names validate.
  - The model is `frozen=True`: events are immutable facts.
- `tests/test_schemas.py`: JSON round-trip, the `class` alias on the wire, the
  optional fields defaulting to None, a missing required field rejected, an
  unknown severity rejected, and immutability enforced.

## Why

Every part of the system (edge buffer, cloud ingestion, alerts, dashboards,
reports) derives from events. Fixing the schema first, with tests that pin the
wire format, keeps both sides honest before either is built.

## Design notes tied to auth (see 0004)

Attribution is server-side: the cloud derives the site from the authenticated
device and rejects any event whose `site_id`/`camera_id` fall outside that
device's scope. The schema therefore carries no `device_id`, and any request
signature (if adopted in Phase 2) lives in the upload envelope, not inside the
`Event`. So this schema stays faithful to ARCHITECTURE.md section 4 regardless
of how auth lands.

## Files created / modified / deleted

- Created: `shared/__init__.py`, `shared/schemas.py`, `tests/test_schemas.py`,
  `change-logs/0003-shared-event-schema.md`.
- Modified: `change-logs/INDEX.md`.

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass (after adopting `StrEnum` per UP042 and
  `datetime.UTC` per UP017).
- `uv run ty check`: pass.
- `uv run pytest`: pass (10 passed).

No suppressions.

## Decisions, biases, tradeoffs

- Applies D-003 (one engine, vertical profiles): `type` and `profile_rule_id`
  are strings so the set of event types grows with each profile without the
  engine hardcoding them.
- Relates to the proposed D-009 (edge/cloud auth, see change-log 0004) through
  the server-side attribution note above.
- No new decision proposed here.
