"""Tests for the SQLite event store."""

from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from edge.events import EventStore
from shared.schemas import Event, Severity


def make_event(event_id: str = "evt-1", **overrides: object) -> Event:
    payload: dict[str, object] = {
        "id": event_id,
        "site_id": "site-dev",
        "camera_id": "camera-1",
        "ts": datetime(2026, 7, 9, 22, 30, tzinfo=UTC),
        "type": "dwell",
        "severity": Severity.info,
        "track_id": 7,
        "zone": "pasillo-3",
        "class": "person",
        "dwell_s": 42.5,
        "profile_rule_id": "dwell",
    }
    payload.update(overrides)
    return Event.model_validate(payload)


def test_insert_read_round_trip(tmp_path: Path) -> None:
    with EventStore(tmp_path / "edge.db") as store:
        event = make_event()
        stored = store.add(event)
        assert stored == event
        assert store.get("evt-1") == event
        assert store.count() == 1


def test_missing_event_is_none(tmp_path: Path) -> None:
    with EventStore(tmp_path / "edge.db") as store:
        assert store.get("nope") is None


def test_snapshot_written_and_referenced(tmp_path: Path) -> None:
    with EventStore(tmp_path / "edge.db") as store:
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        stored = store.add(make_event(), frame=frame)
        assert stored.snapshot_ref is not None
        snapshot = Path(stored.snapshot_ref)
        assert snapshot.exists()
        assert snapshot.name == "evt-1.jpg"
        reread = store.get("evt-1")
        assert reread is not None
        assert reread.snapshot_ref == stored.snapshot_ref


def test_pending_and_mark_uploaded(tmp_path: Path) -> None:
    with EventStore(tmp_path / "edge.db") as store:
        store.add(make_event("evt-1"))
        store.add(make_event("evt-2"))
        assert {e.id for e in store.pending()} == {"evt-1", "evt-2"}

        store.mark_uploaded("evt-1")
        pending = store.pending()
        assert [e.id for e in pending] == ["evt-2"]


def test_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "edge.db"
    with EventStore(db) as store:
        store.add(make_event("evt-1"))
    # A fresh connection to the same file sees the committed event (WAL durability).
    with EventStore(db) as reopened:
        assert reopened.get("evt-1") is not None
        assert reopened.count() == 1
