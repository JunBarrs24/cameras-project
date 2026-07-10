"""Tests for frame ingestion, driven by tiny synthetic videos (no camera)."""

from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest

from edge.ingest import Frame, FrameSource


def make_video(path: Path, n_frames: int, fps: float, size: tuple[int, int]) -> None:
    """Write an MJPG AVI where frame i is filled with value i (for sampling checks)."""
    width, height = size
    fourcc = cv2.VideoWriter.fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    assert writer.isOpened(), "opencv could not open a VideoWriter (codec missing?)"
    for i in range(n_frames):
        writer.write(np.full((height, width, 3), i % 256, dtype=np.uint8))
    writer.release()


def count_raw(path: Path) -> int:
    """How many frames the file actually holds, read straight through cv2."""
    cap = cv2.VideoCapture(str(path))
    n = 0
    while cap.read()[0]:
        n += 1
    cap.release()
    return n


def test_reads_every_frame_when_target_exceeds_source_fps(tmp_path: Path) -> None:
    path = tmp_path / "clip.avi"
    make_video(path, n_frames=12, fps=10, size=(64, 48))
    frames = list(FrameSource(path, target_fps=1000))
    assert len(frames) == count_raw(path)
    assert all(isinstance(f, Frame) for f in frames)
    assert frames[0].image.shape == (48, 64, 3)


def test_samples_down_when_target_below_source_fps(tmp_path: Path) -> None:
    path = tmp_path / "clip.avi"
    make_video(path, n_frames=12, fps=12, size=(32, 24))
    frames = list(FrameSource(path, target_fps=4))  # stride ~3
    raw = count_raw(path)
    assert 0 < len(frames) < raw
    assert 2 <= len(frames) <= 6


def test_frame_index_increases_by_stride(tmp_path: Path) -> None:
    path = tmp_path / "clip.avi"
    make_video(path, n_frames=12, fps=12, size=(16, 16))
    indices = [f.index for f in FrameSource(path, target_fps=4)]
    assert indices == sorted(indices)
    assert indices[0] == 0
    # Constant spacing: the stride between emitted frames is uniform.
    steps = {b - a for a, b in zip(indices, indices[1:], strict=False)}
    assert len(steps) <= 1


def test_clock_is_injectable(tmp_path: Path) -> None:
    path = tmp_path / "clip.avi"
    make_video(path, n_frames=4, fps=4, size=(16, 16))
    fixed = datetime(2026, 7, 9, 22, 30, tzinfo=UTC)
    frames = list(FrameSource(path, target_fps=1000, clock=lambda: fixed))
    assert frames and all(f.ts == fixed for f in frames)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        list(FrameSource(tmp_path / "nope.avi"))


def test_rejects_non_positive_target_fps() -> None:
    with pytest.raises(ValueError, match="target_fps"):
        FrameSource("clip.avi", target_fps=0)


def test_stream_url_is_detected() -> None:
    assert FrameSource("rtsp://user:pass@host/stream").is_stream is True
    assert FrameSource("data/samples/clip.avi").is_stream is False
