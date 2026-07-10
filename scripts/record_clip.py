"""Record a sample clip from the live camera into `data/samples/`.

This is what unblocks camera-free development: run it once against the real
camera, then drive the whole pipeline from the saved file. `data/` is gitignored,
so clips never enter the repository.

    uv run python scripts/record_clip.py --seconds 45 --output data/samples/clip.avi

Credentials come from `.env` through `edge.config`; the RTSP URL is never printed.
"""

import argparse
from pathlib import Path

import cv2

from edge.config import load_camera_config
from edge.ingest import FrameSource


def record(output: Path, seconds: float, fps: float) -> int:
    """Capture `seconds` of camera video into `output`; return frames written."""
    output.parent.mkdir(parents=True, exist_ok=True)
    config = load_camera_config()
    source = FrameSource(config.rtsp_url, target_fps=fps)
    fourcc = cv2.VideoWriter.fourcc(*"MJPG")

    writer: cv2.VideoWriter | None = None
    written = 0
    target_frames = round(seconds * fps)
    print(f"Recording {seconds:g}s at {fps:g} fps to {output} ...")
    try:
        for frame in source:
            if writer is None:
                height, width = frame.image.shape[:2]
                writer = cv2.VideoWriter(str(output), fourcc, fps, (width, height))
                if not writer.isOpened():
                    raise OSError(f"could not open writer for {output}")
            writer.write(frame.image)
            written += 1
            if written >= target_frames:
                break
    finally:
        source.close()
        if writer is not None:
            writer.release()
    print(f"Wrote {written} frames to {output}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a sample clip from the camera."
    )
    parser.add_argument("--seconds", type=float, default=45.0)
    parser.add_argument("--fps", type=float, default=8.0)
    parser.add_argument("--output", type=Path, default=Path("data/samples/clip.avi"))
    args = parser.parse_args()
    record(args.output, args.seconds, args.fps)


if __name__ == "__main__":
    main()
