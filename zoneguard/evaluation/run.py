"""Reproducible detector evaluation.

Usage:
  python -m evaluation.run --video staged.mp4 --annotations annotations/staged.json --model yolox_tiny
  python -m evaluation.run --video staged.mp4 --model yolox_tiny          # no ground truth: latency/resources only

Writes a JSON report and a Markdown summary. Precision/recall are ONLY reported when ground-truth
annotations are supplied. Nothing is estimated or invented.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from .metrics import DetectionCounts, accumulate, match_events, percentile

ROOT = Path(__file__).resolve().parents[1]


def load_annotations(path: Path) -> dict:
    data = json.loads(path.read_text())
    for k in ("frames",):
        if k not in data:
            raise SystemExit(f"annotation file missing '{k}' (see evaluation/README.md)")
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--annotations", type=Path)
    ap.add_argument("--model", default="yolox_tiny")
    ap.add_argument("--model-dir", type=Path, default=ROOT / "models")
    ap.add_argument("--sample-fps", type=float, default=5.0)
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--max-frames", type=int, default=0)
    ap.add_argument("--out", type=Path, default=ROOT / "evaluation" / "reports")
    ap.add_argument("--label", default="", help="dataset label, e.g. 'staged-office-entry-v1 (consented)'")
    args = ap.parse_args(argv)

    from zoneguard_vision.detectors.yolox_onnx import YoloxOnnxDetector
    from zoneguard_vision.pipeline import FramePipeline, PipelineConfig
    from zoneguard_vision.video import iter_sampled_frames, probe_video
    from zoneguard_vision.zones import ZoneSpec

    info = probe_video(args.video)
    ann = load_annotations(args.annotations) if args.annotations else None
    det = YoloxOnnxDetector(args.model_dir / f"{args.model}.onnx", conf_threshold=args.conf)
    zones = [ZoneSpec(z["id"], z["name"], z.get("kind", "area"), [tuple(p) for p in z["points"]])
             for z in (ann or {}).get("zones", [])]
    pipe = FramePipeline(det, PipelineConfig(zones=zones, obstruction_enabled=False))
    gt_by_t = {round(float(f["t"]), 2): [tuple(b) for b in f.get("boxes", [])] for f in (ann or {}).get("frames", [])}

    proc = psutil.Process(os.getpid())
    proc.cpu_percent(None)
    rss_peak = proc.memory_info().rss
    latencies, matched_frames, zone_event_t = [], [], []
    frames = persons = 0
    t0 = time.perf_counter()
    for t, _idx, frame in iter_sampled_frames(args.video, args.sample_fps, max_frames=args.max_frames or None):
        start = time.perf_counter()
        res = pipe.process(frame, t)
        latencies.append((time.perf_counter() - start) * 1000)
        frames += 1
        preds = [(tuple(d["bbox"]), d["confidence"]) for d in res.detections if d["category"] == "person"]
        persons += len(preds)
        zone_event_t += [e["offset_s"] for e in res.events if e["event_type"] == "zone_entry"]
        if ann is not None:
            key = min(gt_by_t, key=lambda k: abs(k - t)) if gt_by_t else None
            if key is not None and abs(key - t) <= 0.5 / args.sample_fps:
                matched_frames.append((preds, gt_by_t[key]))
        rss_peak = max(rss_peak, proc.memory_info().rss)
    wall = time.perf_counter() - t0

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "video": {"file": args.video.name, "duration_s": round(info.duration_s, 2), "resolution": f"{info.width}x{info.height}",
                  "fps": info.fps},
        "dataset_label": args.label or (ann or {}).get("dataset_label", ""),
        "model": {"name": det.info.name, "version": det.info.version, "licence": det.info.licence, "conf_threshold": args.conf},
        "sampling_fps": args.sample_fps,
        "frames_processed": frames,
        "person_detections": persons,
        "latency_ms_p50": percentile(latencies, 0.5),
        "latency_ms_p95": percentile(latencies, 0.95),
        "latency_ms_mean": (sum(latencies) / len(latencies)) if latencies else None,
        "throughput_fps": frames / wall if wall else None,
        "cpu_percent_avg": proc.cpu_percent(None),
        "rss_peak_mb": round(rss_peak / 1e6, 1),
        "host": {"platform": platform.platform(), "cpu_count": psutil.cpu_count(), "python": sys.version.split()[0]},
        "ground_truth": ann is not None,
    }
    if ann is not None:
        counts: DetectionCounts = accumulate(matched_frames, args.iou)
        report.update({
            "annotated_frames_evaluated": len(matched_frames),
            "iou_threshold": args.iou,
            "true_positives": counts.tp, "false_positives": counts.fp, "false_negatives": counts.fn,
            "precision": counts.precision, "recall": counts.recall, "f1": counts.f1,
        })
        if "zone_entries" in ann:
            ev = match_events(zone_event_t, [float(x) for x in ann["zone_entries"]], ann.get("event_tolerance_s", 2.0))
            report["zone_entry_events"] = ev.as_dict()
    else:
        report["note"] = "No ground-truth annotations supplied: precision, recall, FP and FN were NOT computed."

    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"eval-{args.video.stem}-{args.model}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    (args.out / f"{stem}.json").write_text(json.dumps(report, indent=2))
    md = [f"# ZoneGuard detector evaluation — {args.video.name}", "",
          f"- Model: `{report['model']['version']}` ({report['model']['licence']}), conf ≥ {args.conf}",
          f"- Frames processed: {frames} at {args.sample_fps} fps sampling",
          f"- Latency p50/p95: {report['latency_ms_p50']:.1f} / {report['latency_ms_p95']:.1f} ms per frame" if latencies else "- Latency: n/a",
          f"- Throughput: {report['throughput_fps']:.1f} frames/s · CPU avg {report['cpu_percent_avg']:.0f}% · peak RSS {report['rss_peak_mb']} MB",
          f"- Host: {report['host']['platform']} ({report['host']['cpu_count']} CPUs)", ""]
    if ann is not None:
        def f(v):
            return "n/a" if v is None else f"{v:.3f}"
        md += [f"- Annotated frames: {report['annotated_frames_evaluated']} (IoU ≥ {args.iou})",
               f"- TP {report['true_positives']} · FP {report['false_positives']} · FN {report['false_negatives']}",
               f"- Precision {f(report['precision'])} · Recall {f(report['recall'])} · F1 {f(report['f1'])}"]
    else:
        md += ["**No ground truth supplied — precision/recall not measured.**"]
    md += ["", "_Results apply only to this footage and configuration. Not a safety-critical validation._"]
    (args.out / f"{stem}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nreport: {args.out / (stem + '.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
