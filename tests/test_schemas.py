"""Tests for the shared Event schema."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from shared.schemas import Event, Severity


def base_payload(**overrides: object) -> dict[str, object]:
    """A valid event as it arrives on the wire (the JSON field is `class`)."""
    payload: dict[str, object] = {
        "id": "evt-1",
        "site_id": "site-dev",
        "camera_id": "cam-2",
        "ts": datetime(2026, 7, 9, 22, 30, tzinfo=UTC),
        "type": "intrusion",
        "severity": Severity.high,
        "track_id": 7,
        "zone": "trastienda",
        "class": "person",
        "profile_rule_id": "after-hours-intrusion",
    }
    payload.update(overrides)
    return payload


def test_json_round_trip_preserves_all_fields() -> None:
    event = Event.model_validate(
        base_payload(dwell_s=42.5, snapshot_ref="snap/abc.jpg")
    )
    restored = Event.model_validate_json(event.model_dump_json())
    assert restored == event


def test_wire_format_uses_class_key() -> None:
    dumped = Event.model_validate(base_payload()).model_dump(by_alias=True)
    assert dumped["class"] == "person"
    assert "class_name" not in dumped


def test_validates_from_class_alias() -> None:
    event = Event.model_validate(base_payload())
    assert event.class_name == "person"


def test_optional_fields_default_to_none() -> None:
    event = Event.model_validate(base_payload())
    assert event.dwell_s is None
    assert event.snapshot_ref is None


def test_missing_required_field_raises() -> None:
    payload = base_payload()
    del payload["profile_rule_id"]
    with pytest.raises(ValidationError):
        Event.model_validate(payload)


def test_unknown_severity_rejected() -> None:
    with pytest.raises(ValidationError):
        Event.model_validate(base_payload(severity="urgent"))


def test_event_is_immutable() -> None:
    event = Event.model_validate(base_payload())
    with pytest.raises(ValidationError):
        event.zone = "otra-zona"
