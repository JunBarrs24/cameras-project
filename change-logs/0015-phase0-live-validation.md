# 0015: Phase 0 live validation status

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Documentation. Recorded the live validation results and flagged the one
remaining Phase 0 exit criterion as high priority.

- `docs/plans/PHASE_0.md`: added a `Status (2026-07-09)` note before "Out of
  scope". Exit criteria 1, 2, 4, and 5 are met; 2 and 4 were verified live
  against the camera. Criterion 3 is the only one left and is marked high
  priority.

## Why

A live run against the Dahua camera exercised the full pipeline with a real
person in the scene. Standing in `pasillo-1` for 30 seconds produced exactly one
`dwell` event (`track=11`, `dwell=30.0s`), stored in SQLite, with a stable track
id throughout. That verifies exit criterion 4 (the real-world cooldown check) and
criterion 2 (tracked persons plus dwell events) beyond the unit tests.

Criterion 3 (a 10-minute live run without a crash, plus automatic recovery after
briefly disconnecting the camera network) was not run in this session. It is the
endurance and self-healing guarantee the edge box rests on, and nothing later in
the roadmap re-tests it, so it is high priority and must be run before Phase 0 is
treated as closed.

## Files created / modified / deleted

- Created: `change-logs/0015-phase0-live-validation.md`.
- Modified: `docs/plans/PHASE_0.md`, `change-logs/INDEX.md`.

## Validation

- `uv run pre-commit run --all-files`: em-dash guard and the four validators
  pass. No code changed.
- Live: `uv run python -m edge` against the camera stored one dwell event as
  described above (run on the dev Mac, not reproducible in CI).

## Decisions, biases, tradeoffs

- No new decision. Records status against the Phase 0 exit criteria.
