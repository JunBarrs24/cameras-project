"""Tests for detection and tracking.

The class-resolution logic is pure and tested fast. The end-to-end tracking test
needs the weights and a recorded clip, so it is marked `slow` and skips when
either is absent (deselect with `-m 'not slow'`).
"""

from collections import Counter
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path

import pytest

from edge.detect import Track, _resolve_class_ids
from edge.ingest import FrameSource
from edge.profile import load_profile

WEIGHTS = Path("yolo11n.pt")
CLIP = Path("data/samples/clip.avi")


def test_resolve_class_ids_maps_names() -> None:
    names = {0: "person", 1: "bicycle", 2: "car"}
    assert _resolve_class_ids(names, ["person", "car"]) == [0, 2]


def test_resolve_class_ids_rejects_unknown() -> None:
    names = {0: "person"}
    with pytest.raises(ValueError, match="not in model weights"):
        _resolve_class_ids(names, ["no-casco"])


def test_track_is_immutable() -> None:
    track = Track(
        track_id=1,
        class_name="person",
        bbox=(0.0, 0.0, 10.0, 20.0),
        confidence=0.9,
        ts=datetime(2026, 7, 9, tzinfo=UTC),
    )
    with pytest.raises(AttributeError):
        track.track_id = 2  # ty: ignore[invalid-assignment]


@pytest.mark.slow
def test_track_runs_and_filters_to_profile_classes() -> None:
    """Smoke the ultralytics + ByteTrack path: load, resolve classes, run once."""
    if not WEIGHTS.exists():
        pytest.skip("model weights not present")

    import numpy as np

    from edge.detect import Detector
    from edge.ingest import Frame

    profile = load_profile("profiles/retail.yaml")
    detector = Detector(profile.model)
    assert detector.class_ids == [0]  # person is class 0 in stock yolo11

    frame = Frame(
        index=0,
        ts=datetime(2026, 7, 9, tzinfo=UTC),
        image=np.zeros((240, 320, 3), dtype=np.uint8),
    )
    assert detector.track(frame) == []  # a blank frame has nothing to track


@pytest.mark.slow
def test_ids_stay_stable_across_frames() -> None:
    if not WEIGHTS.exists():
        pytest.skip("model weights not present")
    if not CLIP.exists():
        pytest.skip("sample clip not present (record with scripts/record_clip.py)")

    from edge.detect import Detector

    profile = load_profile("profiles/retail.yaml")
    detector = Detector(profile.model)

    seen: Counter[int] = Counter()
    for frame in islice(FrameSource(CLIP, target_fps=8), 20):
        for track in detector.track(frame):
            assert track.class_name == "person"
            seen[track.track_id] += 1

    assert seen, "no tracks produced from the sample clip"
    assert any(count >= 2 for count in seen.values()), "no id persisted across frames"
