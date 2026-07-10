# 0009: Rule engine

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 7. Added the rule engine, which turns zone presence and the clock
into events.

- `edge/rules.py`:
  - `RuleEngine.evaluate(presences, now)` reads the zone engine's current
    presences and evaluates every profile rule against them and the injected
    time, returning `Event` objects.
  - Two retail rule shapes, both expressed in the profile: presence in a zone
    during a schedule window (intrusion) and dwell above a threshold. A rule can
    combine conditions; every present one (zone glob, class, schedule, dwell)
    must hold.
  - Zone matching uses `fnmatch`, so `pasillo-*` in a rule matches `pasillo-7`.
  - `_parse_window` / `_in_window` handle a window that crosses midnight
    ("22:00-07:00"), with the start inclusive and the end exclusive. Schedules
    are pre-parsed at construction, so a malformed schedule raises `RuleError`
    immediately rather than mid-run.
  - Cooldown: a per-(rule, track) timestamp suppresses repeats within
    `cooldown_s` (default 300), so a person standing still produces one event.
    Expired entries are pruned each tick to bound memory.
  - Time and event ids are injected (`now` argument, `make_id` factory), so tests
    are deterministic and the app passes the frame timestamp.
- `edge/zones.py`: `present()` now yields a `Presence` (track_id, zone,
  class_name, dwell_s) instead of a bare tuple, and `_Membership` carries the
  track's class. The rule engine needs the class both to filter (construction's
  `no-casco`) and to stamp the event, so the zone engine now carries it through.
- `tests/test_rules.py`: schedule parsing, same-day and midnight-crossing
  windows with boundary checks, malformed-schedule rejection, intrusion firing
  inside and staying silent outside the window and in other zones, dwell above
  and below threshold, zone-glob match, the class filter, and cooldown
  (suppress within, reopen after, independent per track).
- `tests/test_zones.py`: updated the `present()` assertion to the `Presence`
  shape.

## Why

The rule engine is where zone facts and the clock become the events the whole
product is built on. Keeping evaluation pure (presences and a time in, events
out) makes every rule type unit-testable without a camera, and injecting time
lets tests pin schedule boundaries and cooldown exactly.

## Files created / modified / deleted

- Created: `edge/rules.py`, `tests/test_rules.py`,
  `change-logs/0009-rule-engine.md`.
- Modified: `edge/zones.py`, `tests/test_zones.py`, `change-logs/INDEX.md`.

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass.
- `uv run ty check`: pass. `Event` is built via `model_validate` with a dict,
  because `class` is the field's alias and a Python keyword, so it cannot be a
  constructor keyword.
- `uv run pytest`: pass (54 passed, 1 skipped: the clip-dependent tracking test).

No suppressions.

## Decisions, biases, tradeoffs

- Applies D-003 (one engine, vertical profiles): both rule shapes are profile
  config, so construction's PPE rules reuse the same engine.
- Accepted tradeoff in the cooldown model: it is purely time-based, so a genuine
  re-entry within `cooldown_s` does not re-alert, and a tracking gap (the zone
  engine drops and re-adds a membership) resets dwell. Both favor fewer false and
  duplicate alerts over maximal sensitivity, which suits a security product. If
  the real-camera test in the phase exit criteria shows this is too blunt, it
  becomes a tuning change with its own entry.
- No new decision proposed here.
