"""Tests for the application wiring."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from edge.app import AppSettings, build_app
from edge.zones import ZoneError

WEIGHTS = Path("yolo11n.pt")


def make_video(path: Path, n_frames: int, fps: float = 8.0) -> None:
    fourcc = cv2.VideoWriter.fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (64, 48))
    assert writer.isOpened()
    for _ in range(n_frames):
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()


def test_build_app_unknown_camera_raises_before_loading_model(tmp_path: Path) -> None:
    # Zones load before the detector, so a config error is caught fast (no weights).
    settings = AppSettings(
        source="unused.avi", camera_id="camera-99", db_path=str(tmp_path / "edge.db")
    )
    with pytest.raises(ZoneError, match="not found"):
        build_app(settings)


@pytest.mark.slow
def test_app_runs_over_a_synthetic_clip(tmp_path: Path) -> None:
    if not WEIGHTS.exists():
        pytest.skip("model weights not present")
    clip = tmp_path / "clip.avi"
    make_video(clip, n_frames=6)
    settings = AppSettings(source=str(clip), db_path=str(tmp_path / "edge.db"))
    stored = build_app(settings).run(max_frames=6)
    # Blank frames have no people, so the loop runs clean and stores nothing.
    assert stored == 0
