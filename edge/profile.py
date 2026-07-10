"""Vertical profiles: the only thing that differs per market (ARCHITECTURE.md 3).

A profile declares the model weights and classes, the rules the engine evaluates,
and the report templates. The engine code is single for every client (D-003), so
everything client-specific is expressed here as validated configuration.

The models are strict: unknown keys are rejected so a typo in a profile fails
loudly at load time instead of silently disabling a rule.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from shared.schemas import Severity

_STRICT = ConfigDict(extra="forbid", populate_by_name=True)


class ProfileError(Exception):
    """A profile could not be read or failed validation."""


class ModelSpec(BaseModel):
    """Which weights the detector loads and which classes it keeps."""

    model_config = _STRICT

    weights: str
    classes: list[str]


class RuleWhen(BaseModel):
    """The condition of a rule: a zone plus optional schedule, dwell, or class.

    `class` is a Python keyword, so it is exposed as `class_name` with the `class`
    alias, keeping the yaml faithful to the schema. The rule engine (step 7)
    interprets `schedule` and `dwell_gt_s`; here they are only carried and typed.
    """

    model_config = _STRICT

    zone: str
    schedule: str | None = None
    dwell_gt_s: float | None = None
    class_name: str | None = Field(default=None, alias="class")


class RuleEmit(BaseModel):
    """What a matched rule produces: an event type, severity, and routing."""

    model_config = _STRICT

    type: str
    severity: Severity
    alert: str | None = None
    snapshot: bool = False


class Rule(BaseModel):
    """One profile rule: when the condition holds, emit the event."""

    model_config = _STRICT

    id: str
    when: RuleWhen
    emit: RuleEmit


class Profile(BaseModel):
    """A full vertical profile as loaded from `profiles/<vertical>.yaml`."""

    model_config = _STRICT

    model: ModelSpec
    rules: list[Rule]
    reports: list[str] = Field(default_factory=list)


def load_profile(path: str | Path) -> Profile:
    """Read and validate a profile yaml, raising `ProfileError` on any problem."""
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError(f"could not read profile {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ProfileError(f"profile {path} must be a mapping at the top level")
    try:
        return Profile.model_validate(raw)
    except ValidationError as exc:
        raise ProfileError(f"invalid profile {path}:\n{exc}") from exc
