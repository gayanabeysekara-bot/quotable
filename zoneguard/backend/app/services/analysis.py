"""Uploaded staged-video analysis worker."""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import psutil
from sqlalchemy import select

from ..db import session_factory
from ..models import AnalysisJob, Camera, Event, FrameDetection, Notification, Organisation, VideoUpload, Zone
from . import detectors, dispatch, storage
from .notifications import deliver_pending
from .rule_engine import evaluate_event

log = logging.getLogger("zoneguard.analysis")


def zone_specs(zones: list[Zone]):
    from zoneguard_vision.zones import ZoneSpec

    return [ZoneSpec(str(z.id), z.name, z.kind, [tuple(p) for p in z.points], z.direction)
            for z in zones if z.enabled]


def run_job(job_id) -> None:
    from zoneguard_vision.pipeline import FramePipeline, PipelineConfig
    from zoneguard_vision.video import iter_sampled_frames

    db = session_factory()()
    proc = psutil.Process(os.getpid())
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None or job.status not in ("queued",):
            return
        video = db.get(VideoUpload, job.video_id)
        if video is None or video.deleted_at is not None or not video.storage_key:
            job.status, job.error = "failed", "video no longer available"
            db.commit()
            return
        camera = db.get(Camera, video.camera_id)
        org = db.get(Organisation, job.org_id)
        zones = db.scalars(select(Zone).where(Zone.camera_id == camera.id, Zone.org_id == job.org_id)).all()
        job.status, job.started_at = "running", datetime.now(timezone.utc)
        db.commit()

        person = detectors.get_person_detector(job.model_name)
        # Specialist detectors honour the organisation's opt-in flags at run time.
        weapon_mode = job.weapon_mode if org.weapon_detection_mode != "disabled" else "disabled"
        face_mode = job.face_covering_mode if org.face_covering_mode != "disabled" else "disabled"
        pipeline = FramePipeline(
            person,
            PipelineConfig(zones=zone_specs(zones), privacy_masks=[[tuple(p) for p in m] for m in camera.privacy_masks or []]),
            weapon_detector=detectors.build_weapon(weapon_mode),
            face_covering_detector=detectors.build_face_covering(face_mode),
        )
        job.model_version = person.info.version
        path = storage.path_for(video.storage_key)
        total = max(1.0, video.duration_s * job.sample_fps)
        frames = events = incidents = 0
        infer_ms: list[float] = []
        max_persons = 0
        proc.cpu_percent(None)
        rss_peak = proc.memory_info().rss
        notif_ids = []
        batch: list[FrameDetection] = []
        wall0 = time.perf_counter()
        recorded_at = video.recorded_at if video.recorded_at.tzinfo else video.recorded_at.replace(tzinfo=timezone.utc)
        for offset, idx, frame in iter_sampled_frames(path, job.sample_fps):
            res = pipeline.process(frame, offset)
            frames += 1
            infer_ms.append(res.inference_ms)
            max_persons = max(max_persons, sum(1 for d in res.detections if d["category"] == "person"))
            batch.append(FrameDetection(org_id=job.org_id, job_id=job.id, offset_s=round(offset, 3),
                                        frame_index=idx, detections=res.detections))
            for ev in res.events:
                e = Event(
                    org_id=job.org_id, site_id=video.site_id, camera_id=camera.id,
                    zone_id=uuid.UUID(ev["zone_id"]) if ev["zone_id"] else None,
                    source="upload_analysis", job_id=job.id, event_type=ev["event_type"],
                    occurred_at=recorded_at + timedelta(seconds=ev["offset_s"]), offset_s=ev["offset_s"],
                    track_id=ev["track_id"], confidence=ev["confidence"], bbox=ev["bbox"],
                    model_name=ev["model_name"], model_version=ev["model_version"],
                    model_status=ev["model_status"], simulated=ev["simulated"], attributes=ev["attributes"],
                )
                db.add(e)
                db.flush()
                created = evaluate_event(db, e)
                events += 1
                incidents += len(created)
                db.flush()
            if len(batch) >= 25:
                db.add_all(batch)
                batch = []
                job.progress = min(0.99, frames / total)
                rss_peak = max(rss_peak, proc.memory_info().rss)
                db.commit()
                db.refresh(job)
                if job.status == "cancelled":
                    break
        db.add_all(batch)
        notif_ids = [n.id for n in db.scalars(select(Notification).where(
            Notification.org_id == job.org_id, Notification.status == "queued")).all()]
        wall = time.perf_counter() - wall0
        if job.status != "cancelled":
            job.status = "completed"
        job.progress = 1.0
        job.finished_at = datetime.now(timezone.utc)
        sorted_ms = sorted(infer_ms) or [0.0]
        job.stats = {
            "frames_processed": frames,
            "events": events,
            "incidents_created": incidents,
            "max_persons_in_frame": max_persons,
            "avg_inference_ms": round(sum(infer_ms) / len(infer_ms), 2) if infer_ms else None,
            "p95_inference_ms": round(sorted_ms[int(0.95 * (len(sorted_ms) - 1))], 2),
            "wall_time_s": round(wall, 2),
            "realtime_factor": round((video.duration_s / wall), 2) if wall > 0 else None,
            "cpu_percent_avg": round(proc.cpu_percent(None), 1),
            "rss_peak_mb": round(max(rss_peak, proc.memory_info().rss) / 1e6, 1),
            "weapon_mode": weapon_mode,
            "face_covering_mode": face_mode,
            "person_model_status": person.info.status,
        }
        db.commit()
        if notif_ids:
            dispatch.submit(deliver_pending, notif_ids)
    except Exception as exc:  # noqa: BLE001
        log.exception("analysis job %s failed", job_id)
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = f"{type(exc).__name__}: {exc}"[:1000]
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
