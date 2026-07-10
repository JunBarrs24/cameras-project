"""Draw named zones on a camera frame and write them to a site's `zones.yaml`.

Grabs one frame from a source (a recorded clip or the live camera), lets you
click polygon vertices, and saves the zones. Clicks are captured in pixels and
stored NORMALIZED to [0, 1] by frame width and height, so the zones survive a
resolution change (see docs/DECISIONS.md D-010). The installer clicks in pixels
and never deals with the normalization.

    uv run python scripts/draw_zones.py --source data/samples/clip.avi \
        --camera camera-1 --output sites/dev/zones.yaml

Controls: left click adds a point, `n` closes the current polygon and asks for a
name, `u` undoes the last point, `s` saves and quits, `q` quits without saving.
"""

import argparse
from pathlib import Path

import cv2
import yaml

from edge.ingest import FrameSource


def _grab_frame(source: str):
    """Read the first frame from the source, at native rate."""
    for frame in FrameSource(source, target_fps=1000):
        return frame.image
    raise RuntimeError(f"no frames available from {source}")


def _normalize(
    points: list[tuple[int, int]], width: int, height: int
) -> list[list[float]]:
    """Convert pixel clicks to normalized [x, y] pairs rounded for a readable file."""
    return [[round(x / width, 4), round(y / height, 4)] for x, y in points]


def draw(source: str, camera: str, output: Path) -> None:
    frame = _grab_frame(source)
    height, width = frame.shape[:2]
    zones: list[tuple[str, list[list[float]]]] = []
    points: list[tuple[int, int]] = []

    def on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))

    window = "draw zones (n: name polygon, u: undo, s: save, q: quit)"
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        canvas = frame.copy()
        for _name, polygon in zones:
            pixels = [(int(px * width), int(py * height)) for px, py in polygon]
            for a, b in zip(pixels, pixels[1:] + pixels[:1], strict=False):
                cv2.line(canvas, a, b, (0, 255, 0), 2)
        for a, b in zip(points, points[1:], strict=False):
            cv2.line(canvas, a, b, (0, 200, 255), 1)
        for p in points:
            cv2.circle(canvas, p, 3, (0, 0, 255), -1)
        cv2.imshow(window, canvas)

        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            print("Quit without saving.")
            cv2.destroyAllWindows()
            return
        if key == ord("u") and points:
            points.pop()
        if key == ord("n"):
            if len(points) < 3:
                print("A polygon needs at least 3 points.")
                continue
            name = input("Zone name: ").strip()
            if name:
                zones.append((name, _normalize(points, width, height)))
                print(f"Added zone {name!r} with {len(points)} points.")
            points.clear()
        if key == ord("s"):
            break

    cv2.destroyAllWindows()
    output.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, object] = {}
    if output.exists():
        existing = yaml.safe_load(output.read_text(encoding="utf-8")) or {}
    existing[camera] = [{"name": name, "polygon": polygon} for name, polygon in zones]
    header = (
        "# Zones per camera. Polygon vertices are NORMALIZED to [0.0, 1.0] as\n"
        "# [x, y] fractions of frame width and height (docs/DECISIONS.md D-010).\n"
    )
    output.write_text(
        header + yaml.safe_dump(existing, sort_keys=False), encoding="utf-8"
    )
    print(f"Wrote {len(zones)} zone(s) for {camera} to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw named zones on a camera frame.")
    parser.add_argument("--source", required=True, help="RTSP URL or clip path")
    parser.add_argument("--camera", default="camera-1")
    parser.add_argument("--output", type=Path, default=Path("sites/dev/zones.yaml"))
    args = parser.parse_args()
    draw(args.source, args.camera, args.output)


if __name__ == "__main__":
    main()
