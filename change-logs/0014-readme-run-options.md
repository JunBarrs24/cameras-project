# 0014: README run options

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Documentation only. Expanded the README run section.

- `README.md`: replaced the bare list of CLI flags with a `Run options` table
  giving each flag, its default, and what it does (matching `edge/__main__.py`).
  Added a `What to expect (retail profile)` note describing the two default
  rules (dwell over 30 seconds in a `pasillo-*` zone, and after-hours intrusion
  in `trastienda` between 22:00 and 07:00), that membership is tested on the
  feet, and the `--cooldown 10` trick to retest dwell without waiting.

## Why

The flags were listed by name only, with no defaults or descriptions, and the
profile-driven behavior (when events actually fire) was undocumented, so a reader
could not tell why a daytime run produces no intrusion event or how long to stand
in a zone. The table and note close that gap.

## Files created / modified / deleted

- Created: `change-logs/0014-readme-run-options.md`.
- Modified: `README.md`, `change-logs/INDEX.md`.

## Validation

- `uv run pre-commit run --all-files`: em-dash guard and the four validators
  pass. No code changed.

## Decisions, biases, tradeoffs

- No new decision. The "what to expect" note describes `profiles/retail.yaml`
  behavior, keeping vertical specifics in the profile per D-003.
