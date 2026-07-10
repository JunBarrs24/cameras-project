"""Event store: the local SQLite buffer at the edge (D-011).

Every event is written here first, then uploaded (ARCHITECTURE.md 2), so it
survives an internet outage and syncs on reconnect. The `events` table mirrors
the shared `Event` schema plus an `uploaded` flag the Phase 1 uploader will use.

SQLite is opened in WAL mode: the real failure mode at the edge is a power cut
(the box is unattended and store staff power-cycle it), and WAL keeps the file
consistent across an abrupt stop. Each write commits, so a stored event is
durable before the loop moves on.

When a rule asks for a snapshot (`emit.snapshot`), pass the frame to `add`; the
store writes a JPEG into the snapshot directory and records its path on the
event.
"""

import sqlite3
from pathlib import Path

import cv2
import numpy as np

from shared.schemas import Event

# The wire columns, in order. `class` is the schema's alias (a Python keyword),
# quoted in SQL. `uploaded` is edge-only bookkeeping, not part of `Event`.
_COLUMNS = (
    "id",
    "site_id",
    "camera_id",
    "ts",
    "type",
    "severity",
    "track_id",
    "zone",
    "class",
    "dwell_s",
    "snapshot_ref",
    "profile_rule_id",
)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    track_id INTEGER NOT NULL,
    zone TEXT NOT NULL,
    "class" TEXT NOT NULL,
    dwell_s REAL,
    snapshot_ref TEXT,
    profile_rule_id TEXT NOT NULL,
    uploaded INTEGER NOT NULL DEFAULT 0
)
"""


class EventStore:
    """SQLite-backed buffer of events, with JPEG snapshots on disk."""

    def __init__(
        self, db_path: str | Path, snapshot_dir: str | Path | None = None
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir = (
            Path(snapshot_dir) if snapshot_dir else self.db_path.parent / "snapshots"
        )
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    def __enter__(self) -> "EventStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def add(self, event: Event, frame: np.ndarray | None = None) -> Event:
        """Store an event. If `frame` is given, write its snapshot and record the path.

        Returns the stored event, which carries `snapshot_ref` when a snapshot was
        written. The event is immutable, so a copy is made rather than mutated.
        """
        stored = event
        if frame is not None:
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            path = self.snapshot_dir / f"{event.id}.jpg"
            if not cv2.imwrite(str(path), frame):
                raise OSError(f"could not write snapshot {path}")
            stored = event.model_copy(update={"snapshot_ref": str(path)})

        data = stored.model_dump(mode="json", by_alias=True)
        columns = ", ".join(f'"{c}"' for c in _COLUMNS)
        placeholders = ", ".join("?" for _ in _COLUMNS)
        self._conn.execute(
            f"INSERT INTO events ({columns}) VALUES ({placeholders})",
            [data[c] for c in _COLUMNS],
        )
        self._conn.commit()
        return stored

    def get(self, event_id: str) -> Event | None:
        """Read one event by id, or None if it is not stored."""
        row = self._conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        return self._row_to_event(row) if row is not None else None

    def pending(self) -> list[Event]:
        """Events not yet uploaded, oldest first. The Phase 1 uploader reads these."""
        rows = self._conn.execute(
            "SELECT * FROM events WHERE uploaded = 0 ORDER BY ts"
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def mark_uploaded(self, event_id: str) -> None:
        """Flag an event as uploaded so `pending` stops returning it."""
        self._conn.execute("UPDATE events SET uploaded = 1 WHERE id = ?", (event_id,))
        self._conn.commit()

    def count(self) -> int:
        """Total events stored."""
        return self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        return Event.model_validate({column: row[column] for column in _COLUMNS})
