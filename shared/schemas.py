"""The event schema: the contract between edge and cloud (ARCHITECTURE.md 4).

An `Event` is a small, immutable fact. Everything the cloud does (alerts,
dashboards, reports) is derived from events, so this model is defined once here
and used unchanged on both sides.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Operational severity of an event. Platform concept, not vertical."""

    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Event(BaseModel):
    """One detected fact from a camera.

    `type` and `profile_rule_id` are strings on purpose: the set of event types
    grows with each vertical profile, so the engine never hardcodes them. The
    JSON field is `class` (a Python keyword), exposed here as `class_name` with
    the `class` alias, so the wire format stays faithful to the schema.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    site_id: str
    camera_id: str
    ts: datetime
    type: str
    severity: Severity
    track_id: int
    zone: str
    class_name: str = Field(alias="class")
    dwell_s: float | None = None
    snapshot_ref: str | None = None
    profile_rule_id: str
