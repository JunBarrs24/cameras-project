# 0013: Plan a usable zone editor

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

No code. Roadmap change: scheduled a real improvement to the zone-drawing UX
after using the Phase 0 tool exposed how poor it is.

- `docs/plans/PHASE_1.md`: added `Step 5: usable zone editor` and renumbered the
  old steps 5 and 6 to 6 and 7. The new step targets a browser-based editor
  served locally (laptop or phone on the LAN): draw polygons on the image, name
  each zone inline on the canvas with no terminal, move and delete vertices and
  zones, live foot-anchor membership feedback, saving normalized to
  `sites/<site>/zones.yaml` (D-010).
- `docs/plans/PHASE_2.md`: step 3 now states the cloud dashboard zone editor
  builds on the Phase 1 local editor.
- `scripts/draw_zones.py`: docstring note marking it an interim tool superseded
  by the Phase 1 editor.

## Why

`scripts/draw_zones.py` proved the concept but its UX is unacceptable for a real
install: the zone name is typed in the terminal while the operator is inside the
OpenCV window (a context switch on every polygon), there is no editing or
deleting of placed vertices or zones, no on-canvas labels, and a single frozen
frame. Drawing a dozen zones across several cameras this way is slow and error
prone, which directly threatens the Phase 1 exit criterion of onboarding a site
in under one hour. Phase 1 is where zones are first drawn on real store cameras,
so the improvement is scheduled there, ahead of the pilot.

## Files created / modified / deleted

- Created: `change-logs/0013-plan-zone-editor-ux.md`.
- Modified: `docs/plans/PHASE_1.md`, `docs/plans/PHASE_2.md`,
  `scripts/draw_zones.py`, `tests/test_zones.py`, `change-logs/INDEX.md`.

Note on `tests/test_zones.py`: the dev zones were redrawn with the real tool
during this session, so `test_load_dev_zones` no longer hardcodes the placeholder
name. It now asserts the file loads at least one zone with a valid normalized
polygon, since `sites/dev/zones.yaml` is operator-owned config.

## Validation

- `uv run pre-commit run --all-files`: em-dash guard and the four validators
  pass. The only code touched is a docstring, so behavior is unchanged.

## Decisions, biases, tradeoffs

- No new decision. Applies the existing D-010 (normalized zone coordinates); the
  editor keeps saving normalized so a resolution change never shifts a zone.
- Reinforces D-003 discipline: the editor is generic tooling, not per-client.
