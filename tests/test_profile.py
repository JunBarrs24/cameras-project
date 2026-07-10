"""Tests for the profile loader."""

from pathlib import Path

import pytest

from edge.profile import Profile, ProfileError, load_profile
from shared.schemas import Severity

RETAIL = Path("profiles/retail.yaml")


def write_profile(tmp_path: Path, text: str) -> Path:
    """Write a profile yaml to a temp file and return its path."""
    path = tmp_path / "profile.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_retail_profile_loads() -> None:
    profile = load_profile(RETAIL)
    assert isinstance(profile, Profile)
    assert profile.model.weights == "yolo11n.pt"
    assert profile.model.classes == ["person"]
    assert [rule.id for rule in profile.rules] == ["after-hours-intrusion", "dwell"]
    assert profile.reports == ["traffic-by-hour", "zone-heatmap", "dwell-ranking"]


def test_rule_fields_parse() -> None:
    rules = {rule.id: rule for rule in load_profile(RETAIL).rules}

    intrusion = rules["after-hours-intrusion"]
    assert intrusion.when.zone == "trastienda"
    assert intrusion.when.schedule == "22:00-07:00"
    assert intrusion.emit.type == "intrusion"
    assert intrusion.emit.severity is Severity.high
    assert intrusion.emit.alert == "whatsapp"

    dwell = rules["dwell"]
    assert dwell.when.dwell_gt_s == 30.0
    assert dwell.emit.severity is Severity.info
    assert dwell.emit.snapshot is False


def test_class_condition_uses_alias(tmp_path: Path) -> None:
    path = write_profile(
        tmp_path,
        "model: {weights: ppe-v1.pt, classes: [person, no-casco]}\n"
        "rules:\n"
        "  - id: no-helmet\n"
        "    when: {zone: zona-activa, class: no-casco}\n"
        "    emit: {type: ppe-violation, severity: high, snapshot: true}\n",
    )
    rule = load_profile(path).rules[0]
    assert rule.when.class_name == "no-casco"
    assert rule.emit.snapshot is True


def test_missing_file_raises() -> None:
    with pytest.raises(ProfileError, match="could not read"):
        load_profile("profiles/does-not-exist.yaml")


def test_non_mapping_top_level_raises(tmp_path: Path) -> None:
    path = write_profile(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ProfileError, match="must be a mapping"):
        load_profile(path)


def test_unknown_key_rejected(tmp_path: Path) -> None:
    path = write_profile(
        tmp_path,
        "model: {weights: yolo11n.pt, classes: [person]}\n"
        "rulez: []\n",  # typo: should be `rules`
    )
    with pytest.raises(ProfileError, match="invalid profile"):
        load_profile(path)


def test_unknown_severity_rejected(tmp_path: Path) -> None:
    path = write_profile(
        tmp_path,
        "model: {weights: yolo11n.pt, classes: [person]}\n"
        "rules:\n"
        "  - id: bad\n"
        "    when: {zone: z}\n"
        "    emit: {type: t, severity: urgent}\n",  # not a Severity
    )
    with pytest.raises(ProfileError, match="invalid profile"):
        load_profile(path)


def test_missing_required_field_raises(tmp_path: Path) -> None:
    path = write_profile(
        tmp_path,
        "rules: []\n",  # no `model`
    )
    with pytest.raises(ProfileError, match="invalid profile"):
        load_profile(path)
