from __future__ import annotations

import argparse
import json
import logging
import signal
import sys


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(prog="zoneguard-edge")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="run the edge agent")
    d = sub.add_parser("discover", help="ONVIF WS-Discovery probe on the local network")
    d.add_argument("--report", action="store_true", help="send results to the cloud dashboard")
    s = sub.add_parser("snapshot", help="send ONE privacy-masked still for zone drawing")
    s.add_argument("--camera", required=True)
    sub.add_parser("check", help="verify cloud connectivity and list assigned cameras")
    args = p.parse_args(argv)

    if args.cmd == "discover":
        from .discovery import discover

        devices = discover()
        print(json.dumps(devices, indent=2))
        if args.report:
            from .client import CloudClient
            from .config import EdgeConfig

            CloudClient(EdgeConfig.from_env()).post_discovery(devices)
        return 0

    from .client import CloudClient
    from .config import EdgeConfig

    cfg = EdgeConfig.from_env()
    client = CloudClient(cfg)
    if args.cmd == "check":
        conf = client.get_config()
        print(f"site: {conf['site']['name']}  cameras: {len(conf['cameras'])}")
        for c in conf["cameras"]:
            print(f" - {c['name']} ({c['source_type']}) zones={len(c['zones'])}")
        return 0
    if args.cmd == "snapshot":
        import cv2

        from zoneguard_vision.privacy import apply_privacy_masks

        from .sources import source_for_camera

        cam = next((c for c in client.get_config()["cameras"] if c["id"] == args.camera), None)
        if cam is None:
            print("camera not assigned to this agent", file=sys.stderr)
            return 2
        src = source_for_camera(cam)
        if not src.open():
            print("could not open stream", file=sys.stderr)
            return 1
        frame = src.read()
        src.close()
        if frame is None:
            print("no frame received", file=sys.stderr)
            return 1
        frame = apply_privacy_masks(frame, [[tuple(p) for p in m] for m in cam.get("privacy_masks", [])])
        ok, buf = cv2.imencode(".jpg", frame)
        client.post_snapshot(cam["id"], buf.tobytes())
        print("snapshot uploaded")
        return 0

    from .agent import EdgeAgent

    agent = EdgeAgent(cfg, client)
    signal.signal(signal.SIGTERM, lambda *_: agent.stop())
    signal.signal(signal.SIGINT, lambda *_: agent.stop())
    agent.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
