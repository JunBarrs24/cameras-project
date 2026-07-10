"""Frame ingestion: per-camera capture with reconnection and sampling.

`FrameSource` wraps `cv2.VideoCapture` and yields `Frame` objects. It accepts an
RTSP URL or a local file path. The file path is what makes camera-free
development possible: a recorded clip drives the whole pipeline offline.

Two behaviors matter for the edge box (ARCHITECTURE.md 2):

- Reconnection. A live stream drops; the source reconnects with exponential
  backoff and keeps yielding, so a brief network blip never crashes the run.
- Sampling. Analytics need only 5 to 10 fps. A file is subsampled by frame
  stride from its native fps; a live stream is subsampled by elapsed time.

Camera credentials can live in an RTSP URL, so URLs are always redacted before
they reach a log line or an error message.
"""

import logging
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_CREDENTIALS = re.compile(r"://[^/@]+@")


def _redact(source: str) -> str:
    """Hide `user:pass@` credentials in a stream URL before logging it."""
    return _CREDENTIALS.sub("://***@", source)


@dataclass(frozen=True, slots=True)
class Frame:
    """One sampled frame: its position in the source, a timestamp, and pixels.

    `ts` is the wall clock at capture, carried downstream so tracks and events
    are stamped at ingestion. It comes from an injectable clock so tests can
    freeze it and later stages can replay a clip against a chosen time.
    """

    index: int
    ts: datetime
    image: np.ndarray


def _default_clock() -> datetime:
    return datetime.now(UTC)


class FrameSource:
    """A camera or file as a stream of sampled `Frame` objects.

    Iterate it directly (`for frame in FrameSource(path): ...`). The underlying
    capture is released when iteration ends, when the iterator is closed, or on
    exit from the `with` block.
    """

    def __init__(
        self,
        source: str | Path,
        target_fps: float = 8.0,
        clock: Callable[[], datetime] = _default_clock,
        backoff_initial_s: float = 1.0,
        backoff_max_s: float = 30.0,
        max_connect_attempts: int | None = None,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be positive")
        self.source = str(source)
        self.target_fps = target_fps
        self.clock = clock
        self.backoff_initial_s = backoff_initial_s
        self.backoff_max_s = backoff_max_s
        self.max_connect_attempts = max_connect_attempts
        self.is_stream = "://" in self.source
        self._cap: cv2.VideoCapture | None = None

    def __enter__(self) -> "FrameSource":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the underlying capture if one is open."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __iter__(self) -> Iterator[Frame]:
        return self._frames_stream() if self.is_stream else self._frames_file()

    def _open_file(self) -> cv2.VideoCapture:
        if not Path(self.source).exists():
            raise FileNotFoundError(f"video file not found: {self.source}")
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            cap.release()
            raise OSError(f"could not open video file: {self.source}")
        return cap

    def _connect_stream(self) -> cv2.VideoCapture:
        delay = self.backoff_initial_s
        attempt = 0
        redacted = _redact(self.source)
        while True:
            cap = cv2.VideoCapture(self.source)
            if cap.isOpened():
                return cap
            cap.release()
            attempt += 1
            if (
                self.max_connect_attempts is not None
                and attempt >= self.max_connect_attempts
            ):
                raise ConnectionError(
                    f"could not open stream after {attempt} attempts: {redacted}"
                )
            logger.warning("stream not reachable, retry in %.1fs: %s", delay, redacted)
            time.sleep(delay)
            delay = min(delay * 2, self.backoff_max_s)

    def _frames_file(self) -> Iterator[Frame]:
        cap = self._open_file()
        self._cap = cap
        native_fps = cap.get(cv2.CAP_PROP_FPS)
        stride = max(1, round(native_fps / self.target_fps)) if native_fps > 0 else 1
        try:
            index = 0
            while True:
                ok, image = cap.read()
                if not ok:
                    return
                if index % stride == 0:
                    yield Frame(index=index, ts=self.clock(), image=image)
                index += 1
        finally:
            self.close()

    def _frames_stream(self) -> Iterator[Frame]:
        cap = self._connect_stream()
        self._cap = cap
        period = 1.0 / self.target_fps
        last_emit: float | None = None
        index = 0
        try:
            while True:
                ok, image = cap.read()
                if not ok:
                    logger.warning(
                        "stream read failed, reconnecting: %s", _redact(self.source)
                    )
                    cap.release()
                    cap = self._connect_stream()
                    self._cap = cap
                    last_emit = None
                    continue
                now = time.monotonic()
                if last_emit is None or now - last_emit >= period:
                    last_emit = now
                    yield Frame(index=index, ts=self.clock(), image=image)
                index += 1
        finally:
            self.close()
