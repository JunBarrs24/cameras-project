# 0005: Profile loader

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 3. Added vertical profiles: the loader and the retail profile.

- `edge/__init__.py`: package marker with a one-line purpose.
- `profiles/retail.yaml`: the retail profile from ARCHITECTURE.md section 3
  (stock `yolo11n.pt`, class `person`, an after-hours intrusion rule and a dwell
  rule, three report templates).
- `edge/profile.py`: pydantic models plus a loader.
  - `ModelSpec` (weights, classes), `RuleWhen` (zone, optional schedule,
    dwell_gt_s, class), `RuleEmit` (type, severity, alert, snapshot), `Rule`
    (id, when, emit), and `Profile` (model, rules, reports).
  - `severity` reuses the shared `Severity` enum, so a profile and an emitted
    event speak the same severity vocabulary.
  - `class` is a Python keyword, so `RuleWhen` exposes it as `class_name` with
    the `class` alias, matching the pattern already used in `shared/schemas.py`.
  - Every model sets `extra="forbid"`, so a typo (for example `rulez:` instead
    of `rules:`) fails at load time instead of silently disabling a rule.
  - `load_profile` reads the yaml and validates it, wrapping read errors,
    non-mapping top levels, and validation errors in one `ProfileError` with a
    clear message.
- `tests/test_profile.py`: the retail profile loads and its rule fields parse;
  the `class` alias parses on a construction-style rule; a missing file, a
  non-mapping top level, an unknown key, an unknown severity, and a missing
  required field each raise `ProfileError`.

## Why

The engine is single for every client (D-003); the profile is the only thing
that differs per market. Loading it through strict pydantic models means a
malformed profile is caught early with a readable error, which matters because
profiles are edited per site and per vertical.

## Files created / modified / deleted

- Created: `edge/__init__.py`, `profiles/retail.yaml`, `edge/profile.py`,
  `tests/test_profile.py`, `change-logs/0005-profile-loader.md`.
- Modified: `change-logs/INDEX.md`.

## Validation

- `uv run ruff format .`: pass (9 files unchanged).
- `uv run ruff check .`: pass.
- `uv run ty check`: pass.
- `uv run pytest`: pass (18 passed).

No suppressions.

## Decisions, biases, tradeoffs

- Applies D-003 (one engine, vertical profiles): all client-specific behavior
  lives in the profile, validated here, and the engine never forks per client.
- The strict `extra="forbid"` posture matches the bias of D-004 and the repo
  governance: fail loudly and early rather than run a half-configured rule.
- No new decision proposed here.
