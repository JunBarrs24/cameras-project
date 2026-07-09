"""Tests for the edge camera configuration loader.

The `isolated_env` fixture chdirs to an empty directory and clears the CAMERA_
environment variables, so the developer's local `.env` never leaks into the
assertions: the tests are deterministic on any machine.
"""

from pathlib import Path

import pytest

from edge.config import CameraConfig


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("CAMERA_USERNAME", "CAMERA_PASSWORD", "CAMERA_IP"):
        monkeypatch.delenv(key, raising=False)


def test_rtsp_url_built_from_fields(isolated_env: None) -> None:
    cfg = CameraConfig(username="admin", password="secret", ip="10.0.0.5")
    assert cfg.rtsp_url == (
        "rtsp://admin:secret@10.0.0.5:554/cam/realmonitor?channel=2&subtype=0"
    )


def test_channel_and_subtype_defaults(isolated_env: None) -> None:
    cfg = CameraConfig(username="admin", password="secret")
    assert cfg.rtsp_channel == 2
    assert cfg.rtsp_subtype == 0
    assert cfg.ip == "192.168.100.115"


def test_channel_override_changes_url(isolated_env: None) -> None:
    cfg = CameraConfig(
        username="admin", password="secret", ip="10.0.0.5", rtsp_channel=1
    )
    assert "channel=1" in cfg.rtsp_url
