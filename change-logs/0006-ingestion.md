# 0006: Ingestion

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 4. Added frame ingestion and a clip recorder.

- `edge/ingest.py`: `FrameSource` wrapping `cv2.VideoCapture`, yielding typed
  `Frame` objects (index, ts, image).
  - Accepts an RTSP URL or a local file path. A path is detected by the absence
    of a `://` scheme. The file path is what makes camera-free development
    possible: a recorded clip drives the whole pipeline offline.
  - Reconnection. A live stream reconnects with exponential backoff (initial and
    max delay configurable) and keeps yielding, so a network blip never crashes
    the run. A finite `max_connect_attempts` is available for tests.
  - Sampling to a target fps (default 8, the 5 to 10 fps analytics need). A file
    is subsampled by frame stride computed from its native fps; a live stream is
    subsampled by elapsed monotonic time.
  - `ts` comes from an injectable clock (default `datetime.now(UTC)`), so tests
    freeze it and later stages can replay a clip against a chosen time.
  - Credentials can live in an RTSP URL, so URLs are redacted (`user:pass@` to
    `***@`) before any log line or error message.
- `scripts/record_clip.py`: records a clip from the live camera into
  `data/samples/` (gitignored), reusing `FrameSource` for capture and reading
  credentials through `edge.config`. The RTSP URL is never printed.
- `tests/test_ingest.py`: drives tiny synthetic MJPG videos (no camera). Covers
  reading every frame when the target exceeds the source fps, subsampling below
  it, uniform stride spacing, the injectable clock, a missing file raising,
  rejecting a non-positive target fps, and stream-versus-file detection.

## Why

Ingestion is the head of the pipeline (ARCHITECTURE.md 2). Making it accept a
file, and adding the recorder, is what lets every later step (detect, zones,
rules) be built and tested without the live camera present.

## Files created / modified / deleted

- Created: `edge/ingest.py`, `scripts/record_clip.py`, `tests/test_ingest.py`,
  `change-logs/0006-ingestion.md`.
- Modified: `change-logs/INDEX.md`.
- `.gitignore` already ignores `data/`, so no change was needed there (the plan
  listed it as a modification, but a prior step had already added the rule).

## Validation

- `uv run ruff format .`: pass.
- `uv run ruff check .`: pass.
- `uv run ty check`: pass (used `cv2.VideoWriter.fourcc`, the member ty's cv2
  stubs expose, in place of the untyped `cv2.VideoWriter_fourcc` alias).
- `uv run pytest`: pass (25 passed).

No suppressions. Manual camera recording via `scripts/record_clip.py` is not run
here; it needs the live camera and is exercised when the clip is captured.

## Decisions, biases, tradeoffs

- Serves the Phase 0 goal of a camera-free development loop: the file path in
  `FrameSource` and the recorder together remove the live camera from the inner
  loop.
- Redaction of credentials in URLs continues the posture of `edge/config.py`
  (never print the RTSP URL).
- No new decision proposed here.
