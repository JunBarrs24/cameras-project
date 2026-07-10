# 0008: Zone engine

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 6. Added the zone engine and the tooling to configure zones.

- `edge/zones.py`:
  - `Zone` (name, polygon) with a ray-casting `contains`. Polygon vertices are
    normalized `[0, 1]` (D-010).
  - `anchor_of`: a track's normalized bottom-center (the feet), where a person
    actually stands. `frame_size` is `(width, height)`; the bbox is in pixels,
    so the anchor is normalized here to match the zone.
  - `ZoneEngine`: a per-(track, zone) state machine. `update(tracks, frame_size)`
    emits `ZoneEvent` enter/exit facts, the exit carrying total dwell. `dwell_s`
    and `present()` expose current memberships, which the rule engine (step 7)
    reads each tick for presence and dwell thresholds.
  - `ZoneSpec` plus `load_zones(path, camera_id)`: strict yaml loading. The
    validator rejects a polygon with fewer than 3 points or any vertex outside
    `[0, 1]`, so a de-normalized file fails at load with a clear error.
- `sites/dev/zones.yaml`: one placeholder zone for the dev camera, with a header
  documenting the normalized convention. Redraw against a real frame once a clip
  or the live camera is available.
- `scripts/draw_zones.py`: shows a frame, collects polygon clicks, and writes the
  yaml. Clicks are captured in pixels and stored normalized (converted on save),
  so the installer never handles normalization.
- `tests/test_zones.py`: point-in-polygon, feet-not-center membership, enter,
  exit with total dwell, dwell accumulation across frames, a track crossing two
  zones, re-entry starting a fresh membership, and the loader (dev file plus
  unknown-camera, de-normalized, and too-few-points errors).

## Documentation of the normalized-coordinate decision

Per the request, the normalized convention is documented everywhere it applies:

- Code: module and `Zone`/`anchor_of`/`load_zones` docstrings in `edge/zones.py`,
  and the header and docstring in `scripts/draw_zones.py`.
- Config: a comment block at the top of `sites/dev/zones.yaml`.
- `ARCHITECTURE.md` section 2: the zone-engine bullet now states that zone
  geometry is per site and camera, lives in `sites/<site>/zones.yaml` separate
  from the profile, and is stored normalized (references D-010).
- `docs/DECISIONS.md`: D-010 recorded as validated (see below).

## Why

Zones turn tracks into the facts rules act on. Keeping the engine pure (tracks
and a frame size in, facts out) makes it fully unit-testable and reusable
unchanged in every later phase. Storing geometry per site and camera, referenced
by name from the profile, keeps one engine serving every client (D-003).

## Files created / modified / deleted

- Created: `edge/zones.py`, `sites/dev/zones.yaml`, `scripts/draw_zones.py`,
  `tests/test_zones.py`, `change-logs/0008-zone-engine.md`.
- Modified: `ARCHITECTURE.md`, `docs/DECISIONS.md` (append D-010),
  `change-logs/INDEX.md`.

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass.
- `uv run ty check`: pass.
- `uv run pytest`: pass (41 passed, 1 skipped: the clip-dependent tracking test).

No suppressions. `scripts/draw_zones.py` needs a display and a frame, so it is
run manually when a clip or the camera is available.

## Decisions, biases, tradeoffs

- Applies D-003 (one engine, vertical profiles): zone geometry is site config
  referenced by name from the profile, so the engine never forks per client.
- Proposes and records D-010 (zone polygons in normalized coordinates). The
  developer validated normalized coordinates explicitly in this session, so
  D-010 is appended to `docs/DECISIONS.md` with status `validated`, following the
  governance flow (propose in the change log, then append on explicit
  validation).
