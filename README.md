# proyecto-rafa

Edge video-analytics pipeline: camera in, events out. One engine, one profile per
vertical. See [ARCHITECTURE.md](ARCHITECTURE.md) for the design and
[docs/](docs/) for the rules that govern changes.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/).
- A reachable RTSP camera, or any video file with people moving (development
  works fully from a recorded clip, no camera needed).

## Setup

```bash
uv sync
```

Camera credentials come from a `.env` file at the repo root (gitignored). Copy
the example and fill it in:

```bash
cp .env.example .env
# edit .env: CAMERA_USERNAME, CAMERA_PASSWORD, CAMERA_IP, ...
```

## Record a sample clip (optional, enables camera-free work)

```bash
uv run python -m scripts.record_clip --seconds 45 --output data/samples/clip.avi
```

## Draw zones

Zones are named polygons per camera, stored normalized in `sites/<site>/zones.yaml`
(see D-010 in [docs/DECISIONS.md](docs/DECISIONS.md)). Draw them on a real frame:

```bash
uv run python -m scripts.draw_zones --source data/samples/clip.avi \
    --camera camera-1 --output sites/dev/zones.yaml
```

Left click adds a point, `n` names and closes a polygon, `u` undoes, `s` saves,
`q` quits.

## Run the pipeline

Against a recorded clip:

```bash
uv run python -m edge --source data/samples/clip.avi --show
```

Against the live camera (no `--source`, the RTSP URL is built from `.env`):

```bash
uv run python -m edge --show
```

Events are written to `data/edge.db` (SQLite). Inspect them:

```bash
sqlite3 data/edge.db "select type, zone, track_id, dwell_s, ts from events"
```

Useful flags: `--profile`, `--zones`, `--site`, `--camera`, `--db`, `--fps`,
`--cooldown`, `--max-frames`. Stop a live run with Ctrl-C (it shuts down
gracefully).

## Validate

Every change must pass the four validators (also run by pre-commit and CI):

```bash
uv run ruff format . && uv run ruff check . && uv run ty check && uv run pytest
```

Tests that need the model weights or a clip are marked `slow`; skip them with
`uv run pytest -m 'not slow'`.
