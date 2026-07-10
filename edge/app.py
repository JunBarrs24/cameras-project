"""Application wiring: the edge main loop (ARCHITECTURE.md 2).

Ties the modules together into one loop: ingest a frame, detect and track,
update zones, evaluate rules, store the events. Each stage is built and tested on
its own; this module only sequences them and owns process lifecycle (graceful
shutdown) and an optional annotated debug window.
"""

import logging
import signal
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from edge.detect import Detector, Track
from edge.events import EventStore
from edge.ingest import Frame, FrameSource
from edge.profile import Rule, load_profile
from edge.rules import RuleEngine
from edge.zones import Zone, ZoneEngine, load_zones

logger = logging.getLogger(__name__)

_ZONE_COLOR = (0, 255, 0)
_TRACK_COLOR = (0, 200, 255)


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Everything the loop needs to run against one source."""

    source: str
    profile_path: str = "profiles/retail.yaml"
    zones_path: str = "sites/dev/zones.yaml"
    site_id: str = "dev"
    camera_id: str = "camera-1"
    db_path: str = "data/edge.db"
    target_fps: float = 8.0
    cooldown_s: float = 300.0
    show: bool = False


class EdgeApp:
    """The edge pipeline: ingest, detect/track, zones, rules, store."""

    def __init__(
        self,
        source: FrameSource,
        detector: Detector,
        zone_engine: ZoneEngine,
        rule_engine: RuleEngine,
        store: EventStore,
        rules_by_id: dict[str, Rule],
        show: bool = False,
    ) -> None:
        self.source = source
        self.detector = detector
        self.zone_engine = zone_engine
        self.rule_engine = rule_engine
        self.store = store
        self.rules_by_id = rules_by_id
        self.show = show
        self._stop = False

    def request_stop(self, *_: object) -> None:
        """Ask the loop to finish the current frame and exit."""
        self._stop = True

    def run(self, max_frames: int | None = None) -> int:
        """Run the loop until the source ends, a stop is requested, or max_frames.

        Returns the number of events stored during the run.
        """
        previous = signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)
        stored = 0
        try:
            for index, frame in enumerate(self.source):
                if self._stop:
                    break
                stored += self._process(frame)
                if max_frames is not None and index + 1 >= max_frames:
                    break
        finally:
            self.source.close()
            self.store.close()
            if self.show:
                cv2.destroyAllWindows()
            signal.signal(signal.SIGINT, previous[0])
            signal.signal(signal.SIGTERM, previous[1])
        return stored

    def _process(self, frame: Frame) -> int:
        height, width = frame.image.shape[:2]
        tracks = self.detector.track(frame)
        self.zone_engine.update(tracks, (width, height))
        events = self.rule_engine.evaluate(self.zone_engine.present(), frame.ts)
        for event in events:
            rule = self.rules_by_id.get(event.profile_rule_id)
            wants_snapshot = rule is not None and rule.emit.snapshot
            self.store.add(event, frame.image if wants_snapshot else None)
            logger.info(
                "event type=%s severity=%s zone=%s track=%s dwell=%.1fs",
                event.type,
                event.severity,
                event.zone,
                event.track_id,
                event.dwell_s or 0.0,
            )
        if self.show:
            self._show(frame, tracks)
        return len(events)

    def _show(self, frame: Frame, tracks: list[Track]) -> None:
        height, width = frame.image.shape[:2]
        canvas = frame.image.copy()
        for zone in self.zone_engine.zones:
            pixels = np.array(
                [(int(x * width), int(y * height)) for x, y in zone.polygon],
                dtype=np.int32,
            )
            cv2.polylines(canvas, [pixels], True, _ZONE_COLOR, 2)
        for track in tracks:
            x1, y1, x2, y2 = (int(v) for v in track.bbox)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), _TRACK_COLOR, 2)
            cv2.putText(
                canvas,
                f"{track.class_name} {track.track_id}",
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                _TRACK_COLOR,
                1,
            )
        cv2.imshow("edge", canvas)
        cv2.waitKey(1)


def build_app(settings: AppSettings) -> EdgeApp:
    """Load the profile, zones, and models, and wire the pipeline from settings."""
    profile = load_profile(settings.profile_path)
    zones: list[Zone] = load_zones(settings.zones_path, settings.camera_id)
    detector = Detector(profile.model)
    zone_engine = ZoneEngine(zones)
    rule_engine = RuleEngine(
        profile.rules,
        site_id=settings.site_id,
        camera_id=settings.camera_id,
        cooldown_s=settings.cooldown_s,
    )
    store = EventStore(
        settings.db_path, snapshot_dir=Path(settings.db_path).parent / "snapshots"
    )
    source = FrameSource(settings.source, target_fps=settings.target_fps)
    rules_by_id = {rule.id: rule for rule in profile.rules}
    return EdgeApp(
        source, detector, zone_engine, rule_engine, store, rules_by_id, settings.show
    )
