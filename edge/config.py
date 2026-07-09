"""Edge configuration loaded from the environment (.env at the repo root).

Only the edge box needs these values. Secrets never live in code or git: the
camera credentials come from `.env`, which is gitignored (see `.env.example`).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CameraConfig(BaseSettings):
    """Connection settings for one RTSP camera."""

    model_config = SettingsConfigDict(
        env_prefix="CAMERA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    username: str
    password: str
    ip: str = "192.168.100.115"
    rtsp_channel: int = 2
    rtsp_subtype: int = 0

    @property
    def rtsp_url(self) -> str:
        """Build the RTSP URL. Credentials stay out of logs: never print this."""
        return (
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/"
            f"cam/realmonitor?channel={self.rtsp_channel}&subtype={self.rtsp_subtype}"
        )


def load_camera_config() -> CameraConfig:
    """Load and validate the camera config, raising a clear error if incomplete."""
    return CameraConfig()  # ty: ignore[missing-argument]
