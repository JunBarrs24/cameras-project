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

### Run options

| Flag | Default | What it does |
|---|---|---|
| `--source` | camera from `.env` | RTSP URL or clip path to read frames from |
| `--profile` | `profiles/retail.yaml` | vertical profile (model, classes, rules) |
| `--zones` | `sites/dev/zones.yaml` | per-camera zone polygons |
| `--camera` | `camera-1` | which camera block in the zones file to load |
| `--site` | `dev` | site id stamped on every event |
| `--db` | `data/edge.db` | SQLite path for stored events |
| `--fps` | `8` | target sampling rate (analytics need 5 to 10) |
| `--cooldown` | `300` | seconds before the same (rule, track) can re-fire |
| `--max-frames` | unlimited | stop after N frames, for bounded runs |
| `--show` | off | open the annotated debug window |

Stop a live run with Ctrl-C; it shuts down gracefully.

### What to expect (retail profile)

The default `profiles/retail.yaml` has two rules:

- `dwell`: someone in a `pasillo-*` zone for more than 30 seconds produces one
  `dwell` event (repeats suppressed for `--cooldown` seconds).
- `after-hours-intrusion`: someone in `trastienda` between 22:00 and 07:00
  produces an `intrusion` event. It stays silent outside that window, so it does
  not fire during the day.

Zone membership is tested on a person's feet (the bottom of the box). To retest
dwell without waiting out the cooldown, pass a small value, for example
`--cooldown 10`.

## Validate

Every change must pass the four validators (also run by pre-commit and CI):

```bash
uv run ruff format . && uv run ruff check . && uv run ty check && uv run pytest
```

Tests that need the model weights or a clip are marked `slow`; skip them with
`uv run pytest -m 'not slow'`.
