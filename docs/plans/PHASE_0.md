# Phase 0: working pipeline on one machine

Goal: evolve the current camera script into the full edge pipeline running on the development Mac against one camera, driven by a vertical profile, producing events in a local SQLite database.

## Value delivered

Proves the core concept end to end: camera in, stored events out. At the end of this phase there is a demo that generates real events (zone entry, dwell, after-hours intrusion) from a live camera, which is the seed of every sales conversation. Every later phase reuses these modules unchanged.

## Input (must exist before starting)

- `src/main.py`: RTSP capture, YOLO11n detection, on-screen annotation.
- `yolo11n.pt` weights at repo root.
- One reachable RTSP camera (currently a Dahua-style unit at `192.168.100.115`) or, failing that, any video file with people walking.
- ARCHITECTURE.md sections 2 (pipeline), 3 (profiles), 4 (event schema).

## Required

- Python 3.13 with uv (already in place).
- GitHub remote `https://github.com/JunBarrs24/cameras-project.git` (configured in step 0).
- Dev tooling (ruff, pytest, ty, pre-commit), added in step 1.
- A recorded sample clip (30 to 60 seconds, people moving through the camera view), captured in step 4. It enables all development and testing without the live camera.

## Steps

Each step is one change: it passes validators and writes its change-log entry (see docs/HOW_TO_VALIDATE.md and docs/HOW_TO_LOG_CHANGES.md).

### Step 0: repository configuration (executed at plan creation)

- Remove the hardcoded camera credentials from `src/main.py` **before the first push**, so the secret never enters GitHub history: read them from environment variables, add `.env` to `.gitignore`, provide `.env.example`. The password must also be **rotated on the camera itself**, since it existed in the working tree and conversations.
- Configure the remote and publish:

```bash
git remote add origin https://github.com/JunBarrs24/cameras-project.git
git branch -M main
git push -u origin main
```

Files: `src/main.py` (M), `.gitignore` (M), `.env.example` (C)
Validation: `git remote -v` shows origin; the pushed `src/main.py` on GitHub contains no credentials.

### Step 1: tooling, pre-commit, and CI

- `pyproject.toml`: add runtime deps (`pydantic`, `pydantic-settings`, `pyyaml`) and dev deps (`ruff`, `pytest`, `ty`, `pre-commit`), plus `[tool.ruff]` / `[tool.pytest.ini_options]` config.
- `edge/config.py`: loads camera settings from `.env` with pydantic-settings.
- **Pre-commit integration**: `.pre-commit-config.yaml` with local hooks mirroring every validator, so nothing lands in a commit without passing:
  - `ruff format` and `ruff check` (Python)
  - `ty check` (typecheck, whole project)
  - `pytest` (whole suite; the repo is small enough for this to stay fast)
  - an em-dash guard on markdown files (pygrep for the em-dash character, excluding docs/HOW_TO_WRITE_DOCUMENTS.md which names the character), enforcing the writing rule mechanically
  - Install with `uv run pre-commit install`. Committing with `--no-verify` requires a written justification in the change log.
- **CI**: `.github/workflows/ci.yml` running the same four validators on every push, so the rule holds even for commits made outside a hooked clone.
- Delete the hello-world `main.py` at the repo root.

Files: `pyproject.toml` (M), `.pre-commit-config.yaml` (C), `.github/workflows/ci.yml` (C), `edge/config.py` (C), `main.py` (D)
Validation: `uv sync` succeeds; `uv run pre-commit run --all-files` passes; a test commit containing an em-dash in a doc is rejected by the hook; CI green on GitHub.

### Step 2: shared event schema

- `shared/schemas.py`: `Event` pydantic model exactly as ARCHITECTURE.md section 4 defines it (id, site_id, camera_id, ts, type, severity, track_id, zone, class, dwell_s, snapshot_ref, profile_rule_id).
- Serialization round-trip and required-field tests.

Files: `shared/__init__.py` (C), `shared/schemas.py` (C), `tests/test_schemas.py` (C)
Validation: pytest green, ty clean.

### Step 3: profile loader

- `profiles/retail.yaml` as sketched in ARCHITECTURE.md section 3.
- `edge/profile.py`: pydantic models (`ModelSpec`, `Rule`, `Profile`) plus a loader that validates the yaml and rejects malformed profiles with a clear error.

Files: `profiles/retail.yaml` (C), `edge/__init__.py` (C), `edge/profile.py` (C), `tests/test_profile.py` (C)
Validation: valid profile loads; broken fixture yaml raises the expected error.

### Step 4: ingestion

- `edge/ingest.py`: `FrameSource` wrapping `cv2.VideoCapture`. Accepts an RTSP URL **or a file path** (the file path is what makes camera-free development possible). Automatic reconnection with backoff, frame sampling down to a target of 5 to 10 fps.
- `scripts/record_clip.py`: records the sample clip from the live camera into `data/samples/` (gitignored).

Files: `edge/ingest.py` (C), `scripts/record_clip.py` (C), `tests/test_ingest.py` (C), `.gitignore` (M)
Validation: unit test reads a tiny synthetically generated video; manual run records a clip from the camera.

### Step 5: detection and tracking

- `edge/detect.py`: `Detector` loads weights and class filter from the profile, wraps ultralytics `model.track(persist=True)` (ByteTrack) and emits typed `Track` objects (track_id, class_name, bbox, confidence, ts).
- Test on a few frames of the sample clip asserting IDs stay stable across frames (marked `slow`).

Files: `edge/detect.py` (C), `tests/test_detect.py` (C)
Validation: pytest (including slow marker locally); manual `--show` run displays boxes with persistent IDs.

### Step 6: zone engine

- `edge/zones.py`: `Zone` (name, polygon), membership test on the track's bottom-center anchor, and a per-track state machine producing enter/exit facts with dwell durations. Pure logic, no camera involved, fully unit-testable with synthetic tracks.
- `sites/dev/zones.yaml`: named polygons for the dev camera.
- `scripts/draw_zones.py`: helper that shows a frame, lets you click polygon points, and writes the yaml.

Files: `edge/zones.py` (C), `sites/dev/zones.yaml` (C), `scripts/draw_zones.py` (C), `tests/test_zones.py` (C)
Validation: unit tests cover enter, exit, dwell accumulation, and a track crossing two zones.

### Step 7: rule engine

- `edge/rules.py`: evaluates profile rules against zone facts and the clock. Retail v1 needs two rule types: presence in a zone during a schedule window (intrusion) and dwell above a threshold. Emits `Event` objects. Includes a cooldown per (rule, track) so one person standing still produces one event.
- Time is injected, so tests freeze it.

Files: `edge/rules.py` (C), `tests/test_rules.py` (C)
Validation: unit tests cover both rule types, schedule boundaries (a window crossing midnight), and cooldown behavior.

### Step 8: event store

- `edge/events.py`: SQLite (stdlib `sqlite3`) with an `events` table mirroring the shared schema plus an `uploaded` flag (used by Phase 1), and JPEG snapshot writing into `data/snapshots/` when the rule requests it.

Files: `edge/events.py` (C), `tests/test_events.py` (C), `.gitignore` (M)
Validation: insert/read round-trip tests; snapshot file appears on disk.

### Step 9: application wiring

- `edge/app.py`: the main loop (ingest, detect/track, zones, rules, store), graceful shutdown, optional `--show` debug window with annotations.
- `edge/__main__.py`: `uv run python -m edge --profile profiles/retail.yaml --source <rtsp-or-file> [--show]`.
- Delete `src/` once the new entry point reaches parity with the old script.
- `README.md`: how to configure `.env`, draw zones, and run.

Files: `edge/app.py` (C), `edge/__main__.py` (C), `src/` (D), `README.md` (M)
Validation: full run against the sample clip and against the live camera.

## Phase validation (exit criteria)

1. All validators green locally, in pre-commit, and in CI: `ruff format`, `ruff check`, `ty check`, `pytest`.
2. `python -m edge --source data/samples/clip.mp4` produces tracked persons and dwell events; verified with `sqlite3 data/edge.db "select type, zone, ts from events"`.
3. Live camera run of at least 10 minutes without a crash, and automatic recovery after briefly disconnecting the camera network.
4. Standing inside a defined zone for 30+ seconds generates exactly one dwell event (cooldown verified in the real world, beyond the unit test).
5. Every step has its change-log entry and references its decision IDs.

## Out of scope

No cloud upload, no alerts, no dashboard, single camera, no authentication, no packaging. Those belong to Phase 1 and 2.
