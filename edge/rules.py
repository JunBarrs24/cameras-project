"""Rule engine: turns zone presence and the clock into events.

Each tick the engine reads the zone engine's current presences (ARCHITECTURE.md 2)
and evaluates every profile rule against them and the injected time. Retail v1
needs two rule shapes, both expressed in the profile:

- presence in a zone during a schedule window (intrusion), and
- dwell in a zone above a threshold.

A rule can combine conditions (zone, class, schedule, dwell); all present ones
must hold. A matched (rule, track) emits one `Event`, then a per-(rule, track)
cooldown suppresses repeats so a person standing still produces one event.

Time is injected: `evaluate` takes `now`, so tests freeze it and the app passes
the frame's timestamp.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from fnmatch import fnmatchcase
from uuid import uuid4

from edge.profile import Rule
from edge.zones import Presence
from shared.schemas import Event


class RuleError(Exception):
    """A rule could not be compiled (for example a malformed schedule)."""


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.strip().split(":")
    return time(int(hours), int(minutes))


def _parse_window(spec: str) -> tuple[time, time]:
    """Parse `"22:00-07:00"` into (start, end). Raises `RuleError` if malformed."""
    try:
        start_text, end_text = spec.split("-")
        return _parse_hhmm(start_text), _parse_hhmm(end_text)
    except ValueError as exc:
        raise RuleError(f"malformed schedule {spec!r}, expected 'HH:MM-HH:MM'") from exc


def _in_window(now: time, window: tuple[time, time]) -> bool:
    """Is `now` in the window? Start is inclusive, end exclusive; may cross midnight."""
    start, end = window
    if start <= end:
        return start <= now < end
    return now >= start or now < end  # window wraps past midnight


@dataclass(frozen=True, slots=True)
class _CompiledRule:
    """A profile rule with its schedule pre-parsed, ready to evaluate each tick."""

    rule: Rule
    window: tuple[time, time] | None

    def conditions_hold(self, presence: Presence, now: datetime) -> bool:
        when = self.rule.when
        if not fnmatchcase(presence.zone, when.zone):
            return False
        if when.class_name is not None and presence.class_name != when.class_name:
            return False
        if self.window is not None and not _in_window(now.time(), self.window):
            return False
        if when.dwell_gt_s is not None and presence.dwell_s < when.dwell_gt_s:
            return False
        return True


class RuleEngine:
    """Evaluates profile rules against zone presences and emits events."""

    def __init__(
        self,
        rules: list[Rule],
        site_id: str,
        camera_id: str,
        cooldown_s: float = 300.0,
        make_id: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self.site_id = site_id
        self.camera_id = camera_id
        self._cooldown = timedelta(seconds=cooldown_s)
        self._make_id = make_id
        self._compiled = [
            _CompiledRule(
                rule=rule,
                window=_parse_window(rule.when.schedule)
                if rule.when.schedule
                else None,
            )
            for rule in rules
        ]
        self._last_emit: dict[tuple[str, int], datetime] = {}

    def evaluate(self, presences: Iterable[Presence], now: datetime) -> list[Event]:
        """Emit events for rules that match this tick, honoring the cooldown."""
        presences = list(presences)
        self._prune_cooldowns(now)
        events: list[Event] = []
        for compiled in self._compiled:
            for presence in presences:
                if not compiled.conditions_hold(presence, now):
                    continue
                key = (compiled.rule.id, presence.track_id)
                if key in self._last_emit:
                    continue  # still within cooldown (expired keys were pruned)
                self._last_emit[key] = now
                events.append(self._make_event(compiled.rule, presence, now))
        return events

    def _prune_cooldowns(self, now: datetime) -> None:
        expired = [
            key for key, ts in self._last_emit.items() if now - ts >= self._cooldown
        ]
        for key in expired:
            del self._last_emit[key]

    def _make_event(self, rule: Rule, presence: Presence, now: datetime) -> Event:
        # Built via model_validate because `class` is the field's alias and a
        # Python keyword, so it cannot be passed to the constructor by name.
        return Event.model_validate(
            {
                "id": self._make_id(),
                "site_id": self.site_id,
                "camera_id": self.camera_id,
                "ts": now,
                "type": rule.emit.type,
                "severity": rule.emit.severity,
                "track_id": presence.track_id,
                "zone": presence.zone,
                "class_name": presence.class_name,
                "dwell_s": round(presence.dwell_s, 3),
                "snapshot_ref": None,
                "profile_rule_id": rule.id,
            }
        )
