"""Edge CLI entry point.

    uv run python -m edge --profile profiles/retail.yaml --source data/samples/clip.avi
    uv run python -m edge --show            # no --source: use the camera from .env

With no `--source`, the camera RTSP URL is built from `.env` (see edge.config).
"""

import argparse
import logging

from edge.app import AppSettings, build_app
from edge.config import load_camera_config


def main() -> None:
    parser = argparse.ArgumentParser(prog="edge", description="Run the edge pipeline.")
    parser.add_argument(
        "--source", help="RTSP URL or clip path; defaults to the .env camera"
    )
    parser.add_argument("--profile", default="profiles/retail.yaml")
    parser.add_argument("--zones", default="sites/dev/zones.yaml")
    parser.add_argument("--site", default="dev")
    parser.add_argument("--camera", default="camera-1")
    parser.add_argument("--db", default="data/edge.db")
    parser.add_argument("--fps", type=float, default=8.0)
    parser.add_argument("--cooldown", type=float, default=300.0)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--show", action="store_true", help="annotated debug window")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    source = args.source if args.source else load_camera_config().rtsp_url
    settings = AppSettings(
        source=source,
        profile_path=args.profile,
        zones_path=args.zones,
        site_id=args.site,
        camera_id=args.camera,
        db_path=args.db,
        target_fps=args.fps,
        cooldown_s=args.cooldown,
        show=args.show,
    )
    where = args.source if args.source else "camera (.env)"
    logging.getLogger("edge").info("starting on %s", where)
    stored = build_app(settings).run(max_frames=args.max_frames)
    logging.getLogger("edge").info("stopped, stored %d event(s)", stored)


if __name__ == "__main__":
    main()
