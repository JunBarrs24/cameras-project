# 0007: Detection and tracking

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 5. Added the detector, which turns frames into stable tracks.

- `edge/detect.py`:
  - `Track`: a frozen dataclass (track_id, class_name, bbox as pixel
    `(x1, y1, x2, y2)`, confidence, ts). `ts` is copied from the source frame, so
    every downstream fact carries the ingestion time.
  - `_resolve_class_ids`: maps the profile's class names to the loaded model's
    class indices, raising with the available names on any miss. The profile
    speaks names ("person"); ultralytics filters by index. A name absent from the
    weights is a profile/weights mismatch and fails loudly instead of silently
    detecting nothing.
  - `Detector`: loads the weights from the profile's `ModelSpec`, resolves the
    class filter once, and wraps `model.track(persist=True, tracker="bytetrack.yaml")`.
    `track(frame)` returns the frame's tracks, handling the no-detections case
    (`boxes.id is None`) as an empty list.
- `pyproject.toml`: added `lapx` (imports as `lap`), the linear-assignment
  library ByteTrack needs. Without it `model.track` raises `ModuleNotFoundError`
  at run time. Declared explicitly rather than relying on ultralytics' runtime
  auto-install, which does not fit a uv-locked environment.
- `tests/test_detect.py`:
  - Fast, model-free: class-id resolution and its unknown-class error, and
    `Track` immutability.
  - `slow`, weights only (no clip): a smoke test that loads the detector,
    asserts the retail profile resolves to class `[0]`, and runs `track` on a
    blank frame returning `[]`. The weights are committed, so this runs in CI and
    guards the ultralytics plus ByteTrack path.
  - `slow`, weights and clip: iterates the first frames of the sample clip and
    asserts at least one track id persists across frames. Skips when the clip is
    absent (record it with `scripts/record_clip.py`).

## Why

Tracking is what upgrades detections into identities. A stable id per person is
the precondition for dwell, paths, and unique counting, so it belongs before the
zone and rule engines. Typed `Track` objects keep those later stages free of
ultralytics internals.

## Files created / modified / deleted

- Created: `edge/detect.py`, `tests/test_detect.py`,
  `change-logs/0007-detection-tracking.md`.
- Modified: `pyproject.toml`, `uv.lock`, `change-logs/INDEX.md`.

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass.
- `uv run ty check`: pass (one `# ty: ignore[invalid-assignment]` on the
  deliberate frozen-field write in the immutability test).
- `uv run pytest`: pass (29 passed, 1 skipped: the clip-dependent tracking test).
- Manual: ran `Detector(profile.model).track(...)` on a blank frame end to end,
  confirming `lapx` resolves the ByteTrack import and the class filter yields
  `[0]`.

## Decisions, biases, tradeoffs

- Applies D-003 (one engine, vertical profiles): the model weights and classes
  come from the profile, so construction's fine-tuned PPE weights drop in with no
  code change. `_resolve_class_ids` guards that boundary.
- No new decision proposed. Adding `lapx` is an implementation dependency of
  ByteTrack, not a design choice.
