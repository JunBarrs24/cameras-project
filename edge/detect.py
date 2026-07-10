"""Detection and tracking: frames in, stable per-person tracks out.

`Detector` loads the weights and class filter from the profile (ARCHITECTURE.md 2)
and wraps ultralytics `model.track(persist=True)`, which runs ByteTrack to give
each object a stable id across frames. That id is what makes dwell, paths, and
unique counting possible downstream.

The detector emits typed `Track` objects. It stays free of any camera or file
concern: it takes a `Frame` and returns the tracks in it, stamped with the
frame's timestamp.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

from ultralytics import YOLO

from edge.ingest import Frame
from edge.profile import ModelSpec


@dataclass(frozen=True, slots=True)
class Track:
    """One tracked object in one frame.

    `bbox` is pixel `(x1, y1, x2, y2)`. `ts` is copied from the source frame so
    every downstream fact carries the ingestion time.
    """

    track_id: int
    class_name: str
    bbox: tuple[float, float, float, float]
    confidence: float
    ts: datetime


def _resolve_class_ids(names: Mapping[int, str], classes: Iterable[str]) -> list[int]:
    """Map profile class names to the model's class indices, failing on any miss.

    The profile speaks class names ("person"); ultralytics filters by index. A
    name absent from the loaded weights is a profile/weights mismatch, so it
    raises with the available names rather than silently detecting nothing.
    """
    by_name = {name: index for index, name in names.items()}
    missing = [c for c in classes if c not in by_name]
    if missing:
        raise ValueError(
            f"profile classes not in model weights: {missing}; "
            f"available: {sorted(by_name)}"
        )
    return [by_name[c] for c in classes]


class Detector:
    """Runs detection and tracking for one profile's model."""

    def __init__(self, model_spec: ModelSpec, tracker: str = "bytetrack.yaml") -> None:
        self.model = YOLO(model_spec.weights)
        self.class_ids = _resolve_class_ids(self.model.names, model_spec.classes)
        self.tracker = tracker

    def track(self, frame: Frame) -> list[Track]:
        """Detect and track in one frame, returning its tracked objects."""
        results = self.model.track(
            frame.image,
            persist=True,
            classes=self.class_ids,
            tracker=self.tracker,
            verbose=False,
        )
        boxes = results[0].boxes
        if boxes is None or boxes.id is None:
            return []
        names = self.model.names
        tracks: list[Track] = []
        for xyxy, class_index, track_id, confidence in zip(
            boxes.xyxy.tolist(),
            boxes.cls.tolist(),
            boxes.id.tolist(),
            boxes.conf.tolist(),
            strict=False,
        ):
            x1, y1, x2, y2 = xyxy
            tracks.append(
                Track(
                    track_id=int(track_id),
                    class_name=names[int(class_index)],
                    bbox=(x1, y1, x2, y2),
                    confidence=float(confidence),
                    ts=frame.ts,
                )
            )
        return tracks
