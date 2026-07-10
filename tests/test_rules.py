"""Tests for the rule engine, with time and event ids injected for determinism."""

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta

import pytest

from edge.profile import Rule, RuleEmit, RuleWhen
from edge.rules import RuleEngine, RuleError, _in_window, _parse_window
from edge.zones import Presence
from shared.schemas import Severity

BASE = datetime(2026, 7, 9, 23, 0, 0, tzinfo=UTC)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 9, hour, minute, tzinfo=UTC)


def counter_ids() -> Callable[[], str]:
    state = {"n": 0}

    def make() -> str:
        state["n"] += 1
        return f"evt-{state['n']}"

    return make


INTRUSION = Rule(
    id="after-hours-intrusion",
    when=RuleWhen(zone="trastienda", schedule="22:00-07:00"),
    emit=RuleEmit(type="intrusion", severity=Severity.high, alert="whatsapp"),
)
DWELL = Rule(
    id="dwell",
    when=RuleWhen(zone="pasillo-*", dwell_gt_s=30),
    emit=RuleEmit(type="dwell", severity=Severity.info),
)


def engine(*rules: Rule, cooldown_s: float = 300.0) -> RuleEngine:
    return RuleEngine(
        list(rules),
        site_id="site-dev",
        camera_id="camera-1",
        cooldown_s=cooldown_s,
        make_id=counter_ids(),
    )


def in_trastienda(track_id: int = 1, dwell_s: float = 5.0) -> Presence:
    return Presence(
        track_id=track_id, zone="trastienda", class_name="person", dwell_s=dwell_s
    )


def in_pasillo(
    track_id: int = 1, dwell_s: float = 0.0, zone: str = "pasillo-3"
) -> Presence:
    return Presence(track_id=track_id, zone=zone, class_name="person", dwell_s=dwell_s)


# --- schedule helpers ---


def test_parse_window() -> None:
    assert _parse_window("22:00-07:00") == (time(22, 0), time(7, 0))


def test_window_same_day() -> None:
    window = (time(9, 0), time(18, 0))
    assert _in_window(time(12, 0), window) is True
    assert _in_window(time(8, 59), window) is False
    assert _in_window(time(9, 0), window) is True  # start inclusive
    assert _in_window(time(18, 0), window) is False  # end exclusive


def test_window_crossing_midnight() -> None:
    window = (time(22, 0), time(7, 0))
    assert _in_window(time(23, 0), window) is True
    assert _in_window(time(3, 0), window) is True
    assert _in_window(time(22, 0), window) is True  # start inclusive
    assert _in_window(time(7, 0), window) is False  # end exclusive
    assert _in_window(time(21, 59), window) is False
    assert _in_window(time(12, 0), window) is False


def test_malformed_schedule_raises_on_construction() -> None:
    bad = Rule(
        id="bad",
        when=RuleWhen(zone="z", schedule="10pm-7am"),
        emit=RuleEmit(type="x", severity=Severity.low),
    )
    with pytest.raises(RuleError, match="malformed schedule"):
        engine(bad)


# --- intrusion (presence during a window) ---


def test_intrusion_fires_inside_window() -> None:
    events = engine(INTRUSION).evaluate([in_trastienda()], at(23, 0))
    assert len(events) == 1
    event = events[0]
    assert event.type == "intrusion"
    assert event.severity is Severity.high
    assert event.zone == "trastienda"
    assert event.track_id == 1
    assert event.class_name == "person"
    assert event.profile_rule_id == "after-hours-intrusion"
    assert event.site_id == "site-dev"
    assert event.camera_id == "camera-1"


def test_intrusion_silent_outside_window() -> None:
    events = engine(INTRUSION).evaluate([in_trastienda()], at(12, 0))
    assert events == []


def test_intrusion_ignores_other_zones() -> None:
    events = engine(INTRUSION).evaluate([in_pasillo()], at(23, 0))
    assert events == []


# --- dwell (above a threshold) ---


def test_dwell_fires_above_threshold() -> None:
    events = engine(DWELL).evaluate([in_pasillo(dwell_s=35)], at(12, 0))
    assert len(events) == 1
    assert events[0].type == "dwell"
    assert events[0].dwell_s == pytest.approx(35.0)


def test_dwell_silent_below_threshold() -> None:
    events = engine(DWELL).evaluate([in_pasillo(dwell_s=10)], at(12, 0))
    assert events == []


def test_dwell_zone_glob_matches() -> None:
    events = engine(DWELL).evaluate(
        [in_pasillo(dwell_s=40, zone="pasillo-7")], at(12, 0)
    )
    assert len(events) == 1
    assert events[0].zone == "pasillo-7"


# --- class filter ---


def test_class_filter() -> None:
    rule = Rule(
        id="no-helmet",
        when=RuleWhen(zone="zona-activa", class_name="no-casco"),
        emit=RuleEmit(type="ppe-violation", severity=Severity.high),
    )
    eng = engine(rule)
    person = Presence(track_id=1, zone="zona-activa", class_name="person", dwell_s=1)
    nohelmet = Presence(
        track_id=2, zone="zona-activa", class_name="no-casco", dwell_s=1
    )
    assert eng.evaluate([person], at(12, 0)) == []
    assert len(eng.evaluate([nohelmet], at(12, 0))) == 1


# --- cooldown ---


def test_cooldown_suppresses_repeat_then_reopens() -> None:
    eng = engine(DWELL, cooldown_s=300)
    presence = in_pasillo(dwell_s=35)

    first = eng.evaluate([presence], BASE)
    assert len(first) == 1

    # Same track still standing, within cooldown: no second event.
    within = eng.evaluate([presence], BASE + timedelta(seconds=60))
    assert within == []

    # After the cooldown elapses: fires again.
    after = eng.evaluate([presence], BASE + timedelta(seconds=301))
    assert len(after) == 1


def test_cooldown_is_per_track() -> None:
    eng = engine(DWELL, cooldown_s=300)
    events = eng.evaluate(
        [in_pasillo(track_id=1, dwell_s=35), in_pasillo(track_id=2, dwell_s=35)],
        BASE,
    )
    assert len(events) == 2
    assert {e.track_id for e in events} == {1, 2}
