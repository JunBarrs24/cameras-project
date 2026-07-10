"""Zone engine: named polygons per camera, and a per-track state machine.

A zone is a named polygon. Its vertices are stored in NORMALIZED coordinates,
each in `[0.0, 1.0]` relative to frame width and height, so a zone survives a
change in stream resolution (D-010). A track's membership is tested on its
bottom-center anchor (the feet), which is where a person actually stands.

Per (track, zone) the engine keeps a small state machine and emits enter and
exit facts, the exit carrying the dwell duration. It also exposes the current
dwell of active memberships, which the rule engine (step 7) reads each tick to
evaluate presence and dwell thresholds. This module is pure logic: it takes
tracks and a frame size, never a camera, so it is fully unit-testable.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from edge.detect import Track


class ZoneError(Exception):
    """A zones file could not be read or failed validation."""


class ZoneEventKind(StrEnum):
    """A membership transition."""

    enter = "enter"
    exit = "exit"


@dataclass(frozen=True, slots=True)
class ZoneEvent:
    """A track entering or leaving a zone.

    `dwell_s` is `0.0` on enter and the total seconds inside on exit. `ts` is the
    track timestamp of the transition (on exit, the last time the track was seen
    inside).
    """

    kind: ZoneEventKind
    zone: str
    track_id: int
    ts: datetime
    dwell_s: float


@dataclass(frozen=True, slots=True)
class Zone:
    """A named polygon in normalized `[0, 1]` coordinates (D-010)."""

    name: str
    polygon: tuple[tuple[float, float], ...]

    def contains(self, point: tuple[float, float]) -> bool:
        """Point-in-polygon by ray casting. `point` is normalized like the zone."""
        x, y = point
        inside = False
        n = len(self.polygon)
        j = n - 1
        for i in range(n):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]
            crosses_y = (yi > y) != (yj > y)
            if crosses_y and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside


@dataclass(slots=True)
class _Membership:
    """Internal state for one track inside one zone."""

    enter_ts: datetime
    last_ts: datetime


def anchor_of(track: Track, frame_size: tuple[int, int]) -> tuple[float, float]:
    """Normalized bottom-center of a track's bbox. `frame_size` is (width, height)."""
    width, height = frame_size
    x1, _y1, x2, y2 = track.bbox
    return ((x1 + x2) / 2 / width, y2 / height)


class ZoneEngine:
    """Tracks zone membership across frames and emits enter/exit facts."""

    def __init__(self, zones: list[Zone]) -> None:
        self.zones = zones
        self._inside: dict[tuple[int, str], _Membership] = {}

    def update(
        self, tracks: list[Track], frame_size: tuple[int, int]
    ) -> list[ZoneEvent]:
        """Advance the state machine with this frame's tracks; return transitions."""
        events: list[ZoneEvent] = []
        seen: set[tuple[int, str]] = set()

        for track in tracks:
            point = anchor_of(track, frame_size)
            for zone in self.zones:
                if not zone.contains(point):
                    continue
                key = (track.track_id, zone.name)
                seen.add(key)
                membership = self._inside.get(key)
                if membership is None:
                    self._inside[key] = _Membership(track.ts, track.ts)
                    events.append(
                        ZoneEvent(
                            ZoneEventKind.enter,
                            zone.name,
                            track.track_id,
                            track.ts,
                            0.0,
                        )
                    )
                else:
                    membership.last_ts = track.ts

        for key in list(self._inside):
            if key in seen:
                continue
            track_id, zone_name = key
            membership = self._inside.pop(key)
            dwell = (membership.last_ts - membership.enter_ts).total_seconds()
            events.append(
                ZoneEvent(
                    ZoneEventKind.exit, zone_name, track_id, membership.last_ts, dwell
                )
            )

        return events

    def dwell_s(self, track_id: int, zone_name: str) -> float | None:
        """Current dwell of an active membership, or None if the track is not inside."""
        membership = self._inside.get((track_id, zone_name))
        if membership is None:
            return None
        return (membership.last_ts - membership.enter_ts).total_seconds()

    def present(self) -> Iterator[tuple[int, str, float]]:
        """Yield (track_id, zone, dwell_s) for every active membership.

        The rule engine (step 7) reads this each tick to evaluate presence during
        a schedule window and dwell above a threshold.
        """
        for (track_id, zone_name), membership in self._inside.items():
            yield (
                track_id,
                zone_name,
                (membership.last_ts - membership.enter_ts).total_seconds(),
            )


class ZoneSpec(BaseModel):
    """One zone as written in a site's `zones.yaml`, before validation to a `Zone`."""

    model_config = ConfigDict(extra="forbid")

    name: str
    polygon: list[tuple[float, float]]

    @field_validator("polygon")
    @classmethod
    def _normalized_polygon(
        cls, value: list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        if len(value) < 3:
            raise ValueError("a zone polygon needs at least 3 points")
        for x, y in value:
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                raise ValueError(
                    f"polygon points must be normalized to [0, 1], got ({x}, {y})"
                )
        return value

    def to_zone(self) -> Zone:
        return Zone(name=self.name, polygon=tuple(self.polygon))


def load_zones(path: str | Path, camera_id: str) -> list[Zone]:
    """Load and validate one camera's zones from a site's yaml, raising `ZoneError`."""
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ZoneError(f"could not read zones {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ZoneError(f"zones {path} must be a mapping of camera_id to zones")
    if camera_id not in raw:
        raise ZoneError(f"camera {camera_id!r} not found in {path}; have {sorted(raw)}")
    try:
        specs = [ZoneSpec.model_validate(item) for item in raw[camera_id]]
    except ValidationError as exc:
        raise ZoneError(f"invalid zones for {camera_id!r} in {path}:\n{exc}") from exc
    return [spec.to_zone() for spec in specs]
