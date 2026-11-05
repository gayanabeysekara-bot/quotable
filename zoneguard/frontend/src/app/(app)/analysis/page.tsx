"use client";

import { Download, Play, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form";
import { Badge, Callout, Empty, ErrorText, PageHeader, Spinner, StatusBadge, Table, Td, Th } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { EVENT_LABEL, fmtBytes, fmtOffset, fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Camera, Detection, EventRow, Job, Video } from "@/lib/types";

interface ModelsInfo {
  person: { name: string; description: string; available: boolean; licence: string }[];
  weapon_modes: { name: string; label: string; status: string }[];
  face_covering_modes: { name: string; label: string; status: string }[];
  org_flags: { weapon_detection_mode: string; face_covering_mode: string };
}

function localIsoWithOffset(value: string): string {
  // <input type="datetime-local"> has no zone; attach the browser's current offset explicitly.
  const d = new Date(value);
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  const hh = String(Math.floor(Math.abs(off) / 60)).padStart(2, "0");
  const mm = String(Math.abs(off) % 60).padStart(2, "0");
  return `${value.length === 16 ? value + ":00" : value}${sign}${hh}:${mm}`;
}

function UploadCard({ cameras, onUploaded }: { cameras: Camera[]; onUploaded: (v: Video) => void }) {
  const { p } = useOrg();
  const [cameraId, setCameraId] = useState("");
  const [recordedAt, setRecordedAt] = useState("");
  const [consent, setConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<unknown>(null);
  const uploadCams = cameras.filter((c) => c.source_type === "upload");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setError(null);
    const form = new FormData();
    form.append("camera_id", cameraId);
    form.append("recorded_at", localIsoWithOffset(recordedAt));
    form.append("consent_attested", String(consent));
    form.append("file", file);
    // XHR (not fetch) so we can show upload progress.
    const xhr = new XMLHttpRequest();
    xhr.open("POST", p("/videos"));
    xhr.setRequestHeader("X-Requested-With", "zoneguard");
    xhr.upload.onprogress = (ev) => ev.lengthComputable && setProgress(ev.loaded / ev.total);
    xhr.onload = () => {
      setProgress(null);
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 300) throw new Error(typeof data.detail === "string" ? data.detail : `Upload failed (${xhr.status})`);
        setFile(null);
        onUploaded(data);
      } catch (err) {
        setError(err);
      }
    };
    xhr.onerror = () => { setProgress(null); setError(new Error("Network error during upload")); };
    xhr.send(form);
  };

  return (
    <Card>
      <CardHeader><div><CardTitle>Upload staged footage</CardTitle><CardDescription>MP4, MOV, AVI, MKV or WebM. Validated server-side before storage.</CardDescription></div></CardHeader>
      <CardContent>
        {!uploadCams.length ? <Callout tone="warn">Add a camera with source “Uploaded staged video” first (Cameras page).</Callout> : (
          <form onSubmit={submit} className="space-y-3">
            <Field label="Camera" htmlFor="u-cam">
              <Select id="u-cam" required value={cameraId} onChange={(e) => setCameraId(e.target.value)}>
                <option value="" disabled>Select camera</option>
                {uploadCams.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Recorded at (local time)" htmlFor="u-time" hint="Used to evaluate schedules, e.g. after-hours rules.">
              <Input id="u-time" type="datetime-local" required value={recordedAt} onChange={(e) => setRecordedAt(e.target.value)} />
            </Field>
            <Field label="Video file" htmlFor="u-file">
              <Input id="u-file" type="file" required accept=".mp4,.m4v,.mov,.avi,.mkv,.webm" className="py-1.5" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </Field>
            <Checkbox checked={consent} onChange={(e) => setConsent(e.target.checked)} required
              label={<span className="text-xs text-ink-muted">I confirm this footage is staged or lawfully obtained, people in it consented or were notified as required, and it is not real school CCTV used without explicit approval.</span>} />
            <ErrorText error={error} />
            {progress !== null ? (
              <div className="h-2 overflow-hidden rounded bg-surface-3" role="progressbar" aria-valuenow={Math.round(progress * 100)} aria-valuemin={0} aria-valuemax={100}>
                <div className="h-full bg-teal" style={{ width: `${progress * 100}%` }} />
              </div>
            ) : null}
            <Button type="submit" disabled={!file || !consent || progress !== null}><Upload /> Upload</Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

function Review({ video, job }: { video: Video; job: Job }) {
  const { p, org } = useOrg();
  const dets = useData<{ frames: { t: number; detections: Detection[] }[] }>(job.status === "completed" ? p(`/analyses/${job.id}/detections`) : null);
  const events = useData<EventRow[]>(job.status === "completed" ? p(`/analyses/${job.id}/events`) : null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [t, setT] = useState(0);
  const [playable, setPlayable] = useState(true);
  const frames = dets.data?.frames ?? [];
  const current = useMemo(() => {
    if (!frames.length) return null;
    let lo = 0, hi = frames.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (frames[mid].t < t) lo = mid + 1; else hi = mid;
    }
    const cand = [frames[Math.max(0, lo - 1)], frames[lo]];
    return cand.reduce((a, b) => (Math.abs(a.t - t) <= Math.abs(b.t - t) ? a : b));
  }, [frames, t]);

  const seek = (s: number) => {
    setT(s);
    if (videoRef.current && playable) videoRef.current.currentTime = s;
  };
  const colour = { person: "#2DD4BF", weapon: "#F87171", face_covering: "#7DA6FF" } as const;

  return (
    <div className="grid gap-5 xl:grid-cols-5">
      <div className="xl:col-span-3">
        <div className="relative overflow-hidden rounded-md border border-line bg-black" style={{ aspectRatio: `${video.width}/${video.height}` }}>
          {playable ? (
            <video ref={videoRef} src={p(`/videos/${video.id}/stream`)} controls className="absolute inset-0 h-full w-full"
              onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} onError={() => setPlayable(false)} />
          ) : (
            // Browsers cannot play some containers (e.g. AVI); fall back to server-rendered annotated frames.
            // eslint-disable-next-line @next/next/no-img-element
            <img alt={`Annotated frame at ${fmtOffset(t)}`} className="absolute inset-0 h-full w-full" src={p(`/videos/${video.id}/frame?t=${t.toFixed(2)}&job_id=${job.id}`)} />
          )}
          {playable && current ? (
            <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
              {current.detections.map((d, i) => (
                <rect key={i} x={d.bbox[0]} y={d.bbox[1]} width={d.bbox[2] - d.bbox[0]} height={d.bbox[3] - d.bbox[1]}
                  fill="none" stroke={colour[d.category]} strokeWidth={0.003} />
              ))}
            </svg>
          ) : null}
        </div>
        {!playable ? (
          <div className="mt-2 flex items-center gap-3">
            <input type="range" min={0} max={video.duration_s} step={0.2} value={t} onChange={(e) => setT(Number(e.target.value))} className="flex-1 accent-[#2DD4BF]" aria-label="Seek" />
            <span className="text-xs tabular text-ink-muted">{fmtOffset(t)}</span>
          </div>
        ) : null}
        <div className="mt-3 rounded-md border border-line bg-surface-2 p-3 text-xs">
          <div className="mb-1 text-ink-faint">Detections at {fmtOffset(current?.t ?? t)} ({job.model_version || job.model_name})</div>
          {current?.detections.length ? (
            <ul className="flex flex-wrap gap-2">
              {current.detections.map((d, i) => (
                <li key={i}><Badge tone={d.category === "weapon" ? "critical" : d.category === "face_covering" ? "info" : "teal"}>
                  {d.label}{d.track_id ? ` #${d.track_id}` : ""} · {d.confidence.toFixed(2)}{d.simulated ? " · SIMULATED" : ""}
                </Badge></li>
              ))}
            </ul>
          ) : <span className="text-ink-muted">No detections in this frame.</span>}
        </div>
      </div>
      <div className="xl:col-span-2">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Timestamped events</h3>
          <div className="flex gap-1">
            <Button asChild size="sm" variant="outline"><a href={p(`/analyses/${job.id}/export?format=csv`)}><Download /> CSV</a></Button>
            <Button asChild size="sm" variant="outline"><a href={p(`/analyses/${job.id}/export?format=json`)} target="_blank" rel="noreferrer"><Download /> JSON</a></Button>
          </div>
        </div>
        {events.data?.length ? (
          <ul className="max-h-[420px] space-y-1 overflow-y-auto pr-1">
            {events.data.map((e) => (
              <li key={e.id}>
                <button onClick={() => seek(e.offset_s ?? 0)} className="w-full rounded-md border border-line bg-surface-2 px-3 py-2 text-left text-xs hover:border-teal">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-ink">{EVENT_LABEL[e.event_type] ?? e.event_type}</span>
                    <span className="tabular text-ink-faint">{fmtOffset(e.offset_s)}</span>
                  </div>
                  <div className="mt-0.5 text-ink-muted">
                    {fmtTime(e.occurred_at, org.timezone)}{e.confidence !== null ? ` · conf ${e.confidence.toFixed(2)}` : ""}{e.track_id ? ` · track #${e.track_id}` : ""}
                    {e.simulated ? " · SIMULATED" : ""}
                  </div>
                  <div className="mt-0.5 text-ink-faint">Rule outcome: {e.rule_outcome || "—"}</div>
                </button>
              </li>
            ))}
          </ul>
        ) : events.data ? <Empty title="No zone or specialist events">Define zones for this camera, then re-run the analysis.</Empty> : <Spinner />}
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  const { p, siteId, can } = useOrg();
  const cameras = useData<Camera[]>(p(`/cameras${siteId ? `?site_id=${siteId}` : ""}`));
  const videos = useData<Video[]>(p("/videos"));
  const models = useData<ModelsInfo>(p("/models"));
  const [selected, setSelected] = useState<string | null>(null);
  const jobs = useData<Job[]>(selected ? p(`/analyses?video_id=${selected}`) : null);
  const [opts, setOpts] = useState({ model_name: "yolox_tiny", sample_fps: 5, weapon_mode: "disabled", face_covering_mode: "disabled" });
  const [error, setError] = useState<unknown>(null);
  const video = videos.data?.find((v) => v.id === selected) ?? null;
  const latest = jobs.data?.[0] ?? null;
  const running = latest && (latest.status === "queued" || latest.status === "running");

  useEffect(() => {
    if (!running) return;
    const t = setInterval(jobs.reload, 1500);
    return () => clearInterval(t);
  }, [running, jobs.reload]);

  const start = async () => {
    setError(null);
    try {
      await api(p(`/videos/${selected}/analyses`), { body: opts });
      jobs.reload();
    } catch (e) {
      setError(e);
    }
  };
  const del = async (v: Video) => {
    if (!confirm(`Permanently delete ${v.original_filename}? Detection metadata is kept per retention policy.`)) return;
    await api(p(`/videos/${v.id}`), { method: "DELETE" });
    videos.reload();
  };
  const camName = (id: string) => cameras.data?.find((c) => c.id === id)?.name ?? "—";
  const flags = models.data?.org_flags;

  return (
    <>
      <PageHeader title="Video Analysis" description="Run genuine AI person detection on staged CCTV footage, review bounding boxes and timestamped events, and export metadata." />
      <div className="grid gap-5 lg:grid-cols-3">
        {can("upload_video") ? <UploadCard cameras={cameras.data ?? []} onUploaded={(v) => { videos.reload(); setSelected(v.id); }} /> : null}
        <Card className={can("upload_video") ? "lg:col-span-2" : "lg:col-span-3"}>
          <CardHeader><div><CardTitle>Uploaded videos</CardTitle><CardDescription>Raw footage is deleted automatically after the retention period.</CardDescription></div></CardHeader>
          <CardContent className="p-0">
            {!videos.data ? <div className="p-5"><Spinner /></div> : !videos.data.length ? <div className="p-5"><Empty title="No uploads yet" /></div> : (
              <Table>
                <thead><tr><Th>File</Th><Th>Camera</Th><Th>Recorded</Th><Th>Length</Th><Th /></tr></thead>
                <tbody>
                  {videos.data.map((v) => (
                    <tr key={v.id} className={v.id === selected ? "bg-surface-2" : undefined}>
                      <Td><button className="text-left font-medium hover:text-teal disabled:text-ink-faint" disabled={!!v.deleted_at} onClick={() => setSelected(v.id)}>{v.original_filename}</button>
                        <div className="text-[11px] text-ink-faint">{v.width}×{v.height} · {fmtBytes(v.size_bytes)}{v.deleted_at ? " · deleted" : ""}</div></Td>
                      <Td className="text-ink-muted">{camName(v.camera_id)}</Td>
                      <Td className="text-xs text-ink-muted">{fmtTime(v.recorded_at)}</Td>
                      <Td className="tabular text-xs">{fmtOffset(v.duration_s)}</Td>
                      <Td className="text-right">{can("delete_media") && !v.deleted_at ? <Button size="icon" variant="ghost" aria-label={`Delete ${v.original_filename}`} onClick={() => del(v)}><Trash2 /></Button> : null}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {video ? (
        <Card className="mt-5">
          <CardHeader>
            <div><CardTitle>{video.original_filename}</CardTitle><CardDescription>Camera: {camName(video.camera_id)} · zones configured on this camera are evaluated during analysis.</CardDescription></div>
            {latest ? <StatusBadge status={latest.status} /> : null}
          </CardHeader>
          <CardContent>
            {can("run_analysis") ? (
              <div className="mb-5 grid gap-3 rounded-md border border-line bg-surface-2 p-3 sm:grid-cols-2 lg:grid-cols-5">
                <Field label="Person model" htmlFor="m-model">
                  <Select id="m-model" value={opts.model_name} onChange={(e) => setOpts({ ...opts, model_name: e.target.value })}>
                    {(models.data?.person ?? []).map((m) => <option key={m.name} value={m.name} disabled={!m.available}>{m.name}{m.available ? "" : " (not installed)"}</option>)}
                  </Select>
                </Field>
                <Field label="Frames / second" htmlFor="m-fps">
                  <Select id="m-fps" value={opts.sample_fps} onChange={(e) => setOpts({ ...opts, sample_fps: Number(e.target.value) })}>
                    {[1, 2, 5, 10].map((n) => <option key={n} value={n}>{n}</option>)}
                  </Select>
                </Field>
                <Field label="Weapon module (experimental)" htmlFor="m-weapon">
                  <Select id="m-weapon" value={opts.weapon_mode} disabled={flags?.weapon_detection_mode === "disabled"} onChange={(e) => setOpts({ ...opts, weapon_mode: e.target.value })}>
                    {(models.data?.weapon_modes ?? []).map((m) => <option key={m.name} value={m.name}>{m.label}</option>)}
                  </Select>
                </Field>
                <Field label="Face-covering module" htmlFor="m-face">
                  <Select id="m-face" value={opts.face_covering_mode} disabled={flags?.face_covering_mode === "disabled"} onChange={(e) => setOpts({ ...opts, face_covering_mode: e.target.value })}>
                    {(models.data?.face_covering_modes ?? []).map((m) => <option key={m.name} value={m.name}>{m.label}</option>)}
                  </Select>
                </Field>
                <div className="flex items-end"><Button className="w-full" onClick={start} disabled={!!running || !!video.deleted_at}><Play /> Start analysis</Button></div>
                {flags?.weapon_detection_mode === "disabled" || flags?.face_covering_mode === "disabled" ? (
                  <p className="text-[11px] text-ink-faint sm:col-span-2 lg:col-span-5">Specialist modules are disabled for this organisation. An administrator can opt in under Settings → Privacy.</p>
                ) : null}
                {opts.weapon_mode !== "disabled" ? (
                  <Callout tone="warn" className="sm:col-span-2 lg:col-span-5">
                    Weapon outputs are <strong>possible objects</strong>, not confirmed threats. No validated weapon model is bundled; “simulated” mode produces labelled fake detections for workflow testing only.
                  </Callout>
                ) : null}
              </div>
            ) : null}
            <ErrorText error={error} />
            {latest ? (
              <div className="mb-4">
                {running ? (
                  <div>
                    <div className="mb-1 flex justify-between text-xs text-ink-muted"><span>Analysing with {latest.model_name}…</span><span className="tabular">{Math.round(latest.progress * 100)}%</span></div>
                    <div className="h-2 overflow-hidden rounded bg-surface-3" role="progressbar" aria-valuenow={Math.round(latest.progress * 100)} aria-valuemin={0} aria-valuemax={100}>
                      <div className="h-full bg-teal transition-all" style={{ width: `${latest.progress * 100}%` }} />
                    </div>
                  </div>
                ) : latest.status === "failed" ? <Callout tone="danger" title="Analysis failed">{latest.error}</Callout> : latest.status === "completed" ? (
                  <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-muted">
                    <span>Model <strong className="text-ink">{latest.model_version}</strong></span>
                    <span>Frames <strong className="tabular text-ink">{String(latest.stats.frames_processed)}</strong></span>
                    <span>Avg inference <strong className="tabular text-ink">{String(latest.stats.avg_inference_ms)} ms</strong></span>
                    <span>Events <strong className="tabular text-ink">{String(latest.stats.events)}</strong></span>
                    <span>Incidents <strong className="tabular text-ink">{String(latest.stats.incidents_created)}</strong></span>
                    <span>Peak RSS <strong className="tabular text-ink">{String(latest.stats.rss_peak_mb)} MB</strong></span>
                  </div>
                ) : null}
              </div>
            ) : <p className="text-sm text-ink-muted">No analysis yet. Choose a model and start.</p>}
            {latest?.status === "completed" ? <Review key={latest.id} video={video} job={latest} /> : null}
          </CardContent>
        </Card>
      ) : null}
    </>
  );
}
