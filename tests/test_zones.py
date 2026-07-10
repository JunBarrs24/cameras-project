"""Tests for the zone engine, driven by synthetic tracks (no camera)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from edge.detect import Track
from edge.zones import (
    Zone,
    ZoneEngine,
    ZoneError,
    ZoneEventKind,
    anchor_of,
    load_zones,
)

FRAME = (100, 100)  # width, height; a pixel value doubles as a percent
BASE = datetime(2026, 7, 9, 22, 0, 0, tzinfo=UTC)

# A centered square in normalized coordinates: x and y both in [0.3, 0.7].
CENTER = Zone(name="center", polygon=((0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)))
# Left and right bands for crossing tests.
LEFT = Zone(name="left", polygon=((0.0, 0.0), (0.4, 0.0), (0.4, 1.0), (0.0, 1.0)))
RIGHT = Zone(name="right", polygon=((0.6, 0.0), (1.0, 0.0), (1.0, 1.0), (0.6, 1.0)))


def t(seconds: float) -> datetime:
    return BASE + timedelta(seconds=seconds)


def track_at(track_id: int, cx: float, feet_y: float, ts: datetime) -> Track:
    """A person track whose bottom-center (feet) sits at pixel (cx, feet_y)."""
    return Track(
        track_id=track_id,
        class_name="person",
        bbox=(cx - 5, feet_y - 20, cx + 5, feet_y),
        confidence=0.9,
        ts=ts,
    )


def test_contains_inside_and_outside() -> None:
    assert CENTER.contains((0.5, 0.5)) is True
    assert CENTER.contains((0.1, 0.1)) is False


def test_anchor_is_normalized_bottom_center() -> None:
    track = track_at(1, cx=50, feet_y=50, ts=BASE)
    assert anchor_of(track, FRAME) == (0.5, 0.5)


def test_membership_uses_feet_not_box_center() -> None:
    band = Zone(name="top", polygon=((0.0, 0.0), (1.0, 0.0), (1.0, 0.4), (0.0, 0.4)))
    engine = ZoneEngine([band])
    # Feet below the band even though the box extends up into it: not a member.
    events = engine.update([track_at(1, cx=50, feet_y=50, ts=BASE)], FRAME)
    assert events == []


def test_enter_emits_one_event() -> None:
    engine = ZoneEngine([CENTER])
    events = engine.update([track_at(1, cx=50, feet_y=50, ts=BASE)], FRAME)
    assert len(events) == 1
    assert events[0].kind is ZoneEventKind.enter
    assert events[0].zone == "center"
    assert events[0].dwell_s == 0.0


def test_exit_carries_total_dwell() -> None:
    engine = ZoneEngine([CENTER])
    engine.update([track_at(1, 50, 50, t(0))], FRAME)
    engine.update([track_at(1, 50, 50, t(3))], FRAME)  # still inside
    events = engine.update([], FRAME)  # track gone -> exit
    assert len(events) == 1
    assert events[0].kind is ZoneEventKind.exit
    assert events[0].dwell_s == pytest.approx(3.0)


def test_dwell_accumulates_across_frames() -> None:
    engine = ZoneEngine([CENTER])
    engine.update([track_at(1, 50, 50, t(0))], FRAME)
    engine.update([track_at(1, 50, 50, t(5))], FRAME)
    engine.update([track_at(1, 50, 50, t(10))], FRAME)
    assert engine.dwell_s(1, "center") == pytest.approx(10.0)
    assert list(engine.present()) == [(1, "center", pytest.approx(10.0))]


def test_track_crossing_two_zones() -> None:
    engine = ZoneEngine([LEFT, RIGHT])
    engine.update([track_at(1, cx=20, feet_y=50, ts=t(0))], FRAME)  # in left
    engine.update([track_at(1, cx=20, feet_y=50, ts=t(1))], FRAME)  # still left
    events = engine.update([track_at(1, cx=80, feet_y=50, ts=t(2))], FRAME)  # to right
    kinds = {(e.kind, e.zone): e for e in events}
    assert (ZoneEventKind.exit, "left") in kinds
    assert (ZoneEventKind.enter, "right") in kinds
    assert kinds[(ZoneEventKind.exit, "left")].dwell_s == pytest.approx(1.0)


def test_reenter_starts_a_new_membership() -> None:
    engine = ZoneEngine([CENTER])
    engine.update([track_at(1, 50, 50, t(0))], FRAME)
    engine.update([track_at(1, 10, 10, t(2))], FRAME)  # left the zone -> exit
    events = engine.update([track_at(1, 50, 50, t(5))], FRAME)  # back inside
    assert events[0].kind is ZoneEventKind.enter
    assert engine.dwell_s(1, "center") == pytest.approx(0.0)


def test_load_dev_zones() -> None:
    zones = load_zones("sites/dev/zones.yaml", "camera-1")
    assert [z.name for z in zones] == ["zona-demo"]
    assert all(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for z in zones for x, y in z.polygon)


def test_load_zones_unknown_camera_raises() -> None:
    with pytest.raises(ZoneError, match="not found"):
        load_zones("sites/dev/zones.yaml", "camera-99")


def test_load_zones_rejects_non_normalized(tmp_path: Path) -> None:
    path = tmp_path / "zones.yaml"
    path.write_text(
        "camera-1:\n  - name: bad\n    polygon: [[0.1, 0.1], [200, 0.2], [0.3, 0.9]]\n",
        encoding="utf-8",
    )
    with pytest.raises(ZoneError, match="normalized"):
        load_zones(path, "camera-1")


def test_load_zones_rejects_too_few_points(tmp_path: Path) -> None:
    path = tmp_path / "zones.yaml"
    path.write_text(
        "camera-1:\n  - name: bad\n    polygon: [[0.1, 0.1], [0.2, 0.2]]\n",
        encoding="utf-8",
    )
    with pytest.raises(ZoneError, match="at least 3"):
        load_zones(path, "camera-1")
