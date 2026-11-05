from __future__ import annotations

import csv
import hashlib
import io
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..config import get_settings
from ..db import get_db
from ..deps import OrgContext, get_owned, require
from ..models import AnalysisJob, Camera, Event, FrameDetection, VideoUpload
from ..permissions import Perm
from ..ratelimit import enforce
from ..schemas import AnalysisIn, AnalysisJobOut, EventOut, VideoOut
from ..services import analysis, detectors, dispatch, retention, storage

router = APIRouter(prefix="/api/orgs/{org_id}", tags=["video analysis"])

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


@router.get("/models")
def list_models(ctx: OrgContext = Depends(require(Perm.VIEW))):
    return {
        "person": detectors.available_person_models(),
        "weapon_modes": [
            {"name": "disabled", "label": "Disabled", "status": "default"},
            {"name": "simulated_test", "label": "SIMULATED test mode (not a model)", "status": "simulated"},
            {"name": "coco_knife_unvalidated", "label": "Generic COCO 'knife' class — unvalidated, no firearms",
             "status": "experimental"},
        ],
        "face_covering_modes": [
            {"name": "disabled", "label": "Disabled", "status": "default"},
            {"name": "simulated_test", "label": "SIMULATED test mode (no model bundled)", "status": "simulated"},
        ],
        "org_flags": {"weapon_detection_mode": ctx.org.weapon_detection_mode,
                      "face_covering_mode": ctx.org.face_covering_mode},
    }


@router.post("/videos", response_model=VideoOut, status_code=201)
async def upload_video(
    request: Request,
    camera_id: uuid.UUID = Form(...),
    recorded_at: datetime = Form(...),
    consent_attested: bool = Form(...),
    file: UploadFile = File(...),
    ctx: OrgContext = Depends(require(Perm.UPLOAD_VIDEO)),
    db: Session = Depends(get_db),
):
    """Upload staged, consented CCTV footage for analysis.

    Validation: size limit (streamed), extension allow-list, magic-byte container sniffing,
    decode probe with resolution/duration limits. Stored under a random name, never served raw
    without authentication.
    """
    from zoneguard_vision.video import ALLOWED_EXTENSIONS, VideoValidationError, probe_video, sniff_container

    s = get_settings()
    enforce(request, "upload", 20, 3600, key_extra=str(ctx.org_id))
    if not consent_attested:
        raise HTTPException(422, "Confirm the footage is staged or lawfully obtained with appropriate consent/notice")
    cam = get_owned(db, Camera, camera_id, ctx.org_id, "Camera")
    name = Path(file.filename or "video").name
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if recorded_at.tzinfo is None:
        raise HTTPException(422, "recorded_at must include a timezone offset")
    max_bytes = s.max_upload_mb * 1024 * 1024
    key = storage.new_key(ctx.org_id, ext)
    dest = storage.path_for(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    size = 0
    first = b""
    try:
        with open(dest, "wb") as out:
            while chunk := await file.read(1 << 20):
                if not first:
                    first = chunk[:64]
                    if sniff_container(first) is None:
                        raise HTTPException(415, "File contents are not a supported video container")
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, f"File exceeds the {s.max_upload_mb} MB limit")
                h.update(chunk)
                out.write(chunk)
        if size == 0:
            raise HTTPException(422, "Empty file")
        try:
            info = probe_video(dest, max_duration_s=s.max_video_duration_s)
        except VideoValidationError as e:
            raise HTTPException(422, f"Video rejected: {e}") from e
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    v = VideoUpload(
        org_id=ctx.org_id, site_id=cam.site_id, camera_id=cam.id,
        original_filename=_SAFE_NAME.sub("_", name)[:255], storage_key=key, size_bytes=size,
        sha256=h.hexdigest(), container=info.container, width=info.width, height=info.height, fps=info.fps,
        duration_s=info.duration_s, recorded_at=recorded_at, consent_attested=True, uploaded_by=ctx.user.id,
    )
    db.add(v)
    db.flush()
    audit.record(db, "video.uploaded", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="video", target_id=v.id, request=request,
                 details={"camera_id": str(cam.id), "size_bytes": size, "sha256": v.sha256, "consent_attested": True})
    db.commit()
    return v


@router.get("/videos", response_model=list[VideoOut])
def list_videos(camera_id: uuid.UUID | None = None, ctx: OrgContext = Depends(require(Perm.VIEW)),
                db: Session = Depends(get_db)):
    q = select(VideoUpload).where(VideoUpload.org_id == ctx.org_id)
    if camera_id:
        q = q.where(VideoUpload.camera_id == camera_id)
    return db.scalars(q.order_by(VideoUpload.created_at.desc()).limit(200)).all()


@router.get("/videos/{video_id}", response_model=VideoOut)
def get_video(video_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return get_owned(db, VideoUpload, video_id, ctx.org_id, "Video")


@router.delete("/videos/{video_id}")
def delete_video(video_id: uuid.UUID, request: Request, ctx: OrgContext = Depends(require(Perm.DELETE_MEDIA)),
                 db: Session = Depends(get_db)):
    v = get_owned(db, VideoUpload, video_id, ctx.org_id, "Video")
    retention.purge_video(db, v)
    audit.record(db, "video.deleted", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="video", target_id=v.id, request=request)
    db.commit()
    return {"ok": True}


@router.get("/videos/{video_id}/stream")
def stream_video(video_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    v = get_owned(db, VideoUpload, video_id, ctx.org_id, "Video")
    if not v.storage_key or v.deleted_at:
        raise HTTPException(410, "Video has been deleted under the retention policy")
    media = {"mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo",
             "mkv": "video/x-matroska", "webm": "video/webm"}.get(v.container, "application/octet-stream")
    return FileResponse(storage.path_for(v.storage_key), media_type=media,
                        headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline"})


@router.get("/videos/{video_id}/frame")
def annotated_frame(video_id: uuid.UUID, t: float = 0.0, job_id: uuid.UUID | None = None,
                    ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    """JPEG of the frame nearest ``t`` with that frame's stored detections drawn on it."""
    from zoneguard_vision.privacy import apply_privacy_masks
    from zoneguard_vision.video import read_frame_at

    v = get_owned(db, VideoUpload, video_id, ctx.org_id, "Video")
    if not v.storage_key or v.deleted_at:
        raise HTTPException(410, "Video has been deleted under the retention policy")
    frame = read_frame_at(storage.path_for(v.storage_key), t)
    if frame is None:
        raise HTTPException(404, "Frame not available")
    cam = db.get(Camera, v.camera_id)
    frame = apply_privacy_masks(frame, [[tuple(p) for p in m] for m in (cam.privacy_masks or [])])
    if job_id:
        job = get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")
        fd = db.scalar(select(FrameDetection).where(FrameDetection.job_id == job.id)
                       .order_by(func_abs(FrameDetection.offset_s - t)).limit(1))
        if fd:
            h, w = frame.shape[:2]
            colours = {"person": (180, 200, 20), "weapon": (40, 40, 230), "face_covering": (200, 160, 60)}
            for d in fd.detections:
                x1, y1, x2, y2 = d["bbox"]
                c = colours.get(d.get("category"), (255, 255, 255))
                cv2.rectangle(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), c, 2)
                label = f"{d['label']} {d['confidence']:.2f}" + (f" #{d['track_id']}" if d.get("track_id") else "")
                cv2.putText(frame, label, (int(x1 * w), max(12, int(y1 * h) - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return Response(buf.tobytes(), media_type="image/jpeg", headers={"Cache-Control": "private, no-store"})


def func_abs(expr):
    from sqlalchemy import func

    return func.abs(expr)


@router.post("/videos/{video_id}/analyses", response_model=AnalysisJobOut, status_code=202)
def start_analysis(video_id: uuid.UUID, body: AnalysisIn, request: Request,
                   ctx: OrgContext = Depends(require(Perm.RUN_ANALYSIS)), db: Session = Depends(get_db)):
    v = get_owned(db, VideoUpload, video_id, ctx.org_id, "Video")
    if not v.storage_key or v.deleted_at:
        raise HTTPException(410, "Video has been deleted under the retention policy")
    models = {m["name"]: m for m in detectors.available_person_models()}
    if detectors.person_detector_factory is None:
        if body.model_name not in models:
            raise HTTPException(422, f"Unknown model. Choose one of {sorted(models)}")
        if not models[body.model_name]["available"]:
            raise HTTPException(503, f"Model file for {body.model_name} is not installed on the server")
    if body.weapon_mode != "disabled" and ctx.org.weapon_detection_mode == "disabled":
        raise HTTPException(403, "Weapon detection is disabled for this organisation (Settings → Privacy)")
    if body.face_covering_mode != "disabled" and ctx.org.face_covering_mode == "disabled":
        raise HTTPException(403, "Face-covering detection is disabled for this organisation (Settings → Privacy)")
    running = db.scalar(select(AnalysisJob).where(AnalysisJob.video_id == v.id,
                                                  AnalysisJob.status.in_(("queued", "running"))))
    if running:
        raise HTTPException(409, "An analysis is already in progress for this video")
    job = AnalysisJob(org_id=ctx.org_id, video_id=v.id, model_name=body.model_name, sample_fps=body.sample_fps,
                      weapon_mode=body.weapon_mode, face_covering_mode=body.face_covering_mode,
                      requested_by=ctx.user.id)
    db.add(job)
    db.flush()
    audit.record(db, "analysis.started", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="analysis_job", target_id=job.id, request=request, details=body.model_dump())
    db.commit()
    dispatch.submit(analysis.run_job, job.id)
    db.refresh(job)
    return job


@router.get("/analyses", response_model=list[AnalysisJobOut])
def list_jobs(video_id: uuid.UUID | None = None, ctx: OrgContext = Depends(require(Perm.VIEW)),
              db: Session = Depends(get_db)):
    q = select(AnalysisJob).where(AnalysisJob.org_id == ctx.org_id)
    if video_id:
        q = q.where(AnalysisJob.video_id == video_id)
    return db.scalars(q.order_by(AnalysisJob.created_at.desc()).limit(100)).all()


@router.get("/analyses/{job_id}", response_model=AnalysisJobOut)
def get_job(job_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")


@router.post("/analyses/{job_id}/cancel", response_model=AnalysisJobOut)
def cancel_job(job_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.RUN_ANALYSIS)), db: Session = Depends(get_db)):
    job = get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")
    if job.status in ("queued", "running"):
        job.status = "cancelled"
        db.commit()
    return job


@router.get("/analyses/{job_id}/detections")
def job_detections(job_id: uuid.UUID, offset: int = 0, limit: int = 2000,
                   ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    job = get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")
    rows = db.scalars(select(FrameDetection).where(FrameDetection.job_id == job.id)
                      .order_by(FrameDetection.offset_s).offset(max(0, offset)).limit(min(max(1, limit), 5000))).all()
    return {"job_id": str(job.id), "model_name": job.model_name, "model_version": job.model_version,
            "frames": [{"t": r.offset_s, "frame_index": r.frame_index, "detections": r.detections} for r in rows]}


@router.get("/analyses/{job_id}/events", response_model=list[EventOut])
def job_events(job_id: uuid.UUID, ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    job = get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")
    return db.scalars(select(Event).where(Event.job_id == job.id, Event.org_id == ctx.org_id)
                      .order_by(Event.occurred_at)).all()


@router.get("/analyses/{job_id}/export")
def export_job(job_id: uuid.UUID, format: str = "csv", request: Request = None,
               ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    """Export event METADATA only (no imagery)."""
    job = get_owned(db, AnalysisJob, job_id, ctx.org_id, "Analysis job")
    events = db.scalars(select(Event).where(Event.job_id == job.id).order_by(Event.occurred_at)).all()
    audit.record(db, "analysis.exported", org_id=ctx.org_id, actor_user_id=ctx.user.id, actor_label=ctx.user.email,
                 target_type="analysis_job", target_id=job.id, request=request, details={"format": format})
    db.commit()
    rows = [{
        "event_id": str(e.id), "event_type": e.event_type, "occurred_at": e.occurred_at.isoformat(),
        "video_offset_s": e.offset_s, "zone_id": str(e.zone_id) if e.zone_id else "", "track_id": e.track_id,
        "confidence": e.confidence, "bbox": "" if not e.bbox else " ".join(map(str, e.bbox)),
        "model_name": e.model_name, "model_version": e.model_version, "model_status": e.model_status,
        "simulated": e.simulated, "rule_outcome": e.rule_outcome,
    } for e in events]
    if format == "json":
        return {"job": AnalysisJobOut.model_validate(job).model_dump(mode="json"), "events": rows}
    buf = io.StringIO()
    fields = list(rows[0].keys()) if rows else ["event_id", "event_type", "occurred_at"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: _csv_safe(v) for k, v in r.items()})
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="zoneguard-events-{job.id}.csv"'})


def _csv_safe(v):
    """Neutralise spreadsheet formula injection."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


@router.get("/events", response_model=list[EventOut])
def list_events(camera_id: uuid.UUID | None = None, event_type: str | None = None, limit: int = 200,
                ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    q = select(Event).where(Event.org_id == ctx.org_id)
    if camera_id:
        q = q.where(Event.camera_id == camera_id)
    if event_type:
        q = q.where(Event.event_type == event_type)
    return db.scalars(q.order_by(Event.occurred_at.desc()).limit(min(max(limit, 1), 1000))).all()


