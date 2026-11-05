"use client";

import { Pencil, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { PolygonEditor } from "@/components/polygon-editor";
import { ScheduleEditor } from "@/components/schedule-editor";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form";
import { Badge, Callout, Empty, ErrorText, PageHeader, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { describeWindows } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Camera, Point, Window, Zone } from "@/lib/types";

const EXAMPLES = ["Finance office", "Administration office", "Restricted storage", "Medication storage", "Records room", "Staff-only entrance"];

type Draft = { id?: string; name: string; kind: "area" | "line"; points: Point[]; direction: Zone["direction"];
  monitoring_schedule: Window[]; approved_access: Window[]; enabled: boolean; quickRule: boolean };

const blank = (): Draft => ({ name: "", kind: "area", points: [], direction: "any", monitoring_schedule: [],
  approved_access: [{ days: [0, 1, 2, 3, 4], start: "08:00", end: "17:00" }], enabled: true, quickRule: true });

export default function ZonesPage() {
  const { p, siteId, can } = useOrg();
  const cameras = useData<Camera[]>(p(`/cameras${siteId ? `?site_id=${siteId}` : ""}`));
  const [cameraId, setCameraId] = useState("");
  const zones = useData<Zone[]>(cameraId ? p(`/zones?camera_id=${cameraId}`) : null);
  const [d, setD] = useState<Draft>(blank());
  const [error, setError] = useState<unknown>(null);
  const [saved, setSaved] = useState("");
  const editable = can("manage_zones_rules");

  useEffect(() => {
    if (!cameraId && cameras.data?.length) setCameraId(cameras.data[0].id);
  }, [cameras.data, cameraId]);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved("");
    try {
      const body = { name: d.name, points: d.points, direction: d.direction, monitoring_schedule: d.monitoring_schedule,
        approved_access: d.approved_access, enabled: d.enabled };
      if (d.id) {
        await api(p(`/zones/${d.id}`), { method: "PATCH", body });
      } else {
        const z = await api<Zone>(p("/zones"), { body: { ...body, camera_id: cameraId, kind: d.kind } });
        if (d.quickRule) {
          await api(p("/rules"), { body: {
            name: `${z.name} — after hours`, event_type: d.kind === "line" ? "line_crossing" : "zone_entry",
            camera_id: cameraId, zone_id: z.id, schedule: [{ days: [0, 1, 2, 3, 4, 5, 6], start: "18:00", end: "06:00" }],
            severity: "review_required", suppression_seconds: 300,
          } });
        }
      }
      setSaved(d.id ? "Zone updated." : d.quickRule ? "Zone and after-hours rule created." : "Zone created.");
      setD(blank());
      zones.reload();
    } catch (err) {
      setError(err);
    }
  };

  const remove = async (z: Zone) => {
    if (!confirm(`Delete zone "${z.name}" and its rules?`)) return;
    await api(p(`/zones/${z.id}`), { method: "DELETE" });
    zones.reload();
  };

  const minPts = d.kind === "line" ? 2 : 3;
  return (
    <>
      <PageHeader title="Zone Configuration" description="Draw restricted areas and entrance boundaries on the camera view. A detection inside a zone is evidence of possible entry — not proof that anyone was unauthorised." />
      {!cameras.data ? <Spinner /> : !cameras.data.length ? <Empty title="No cameras">Add a camera first.</Empty> : (
        <div className="grid gap-5 lg:grid-cols-5">
          <Card className="lg:col-span-3">
            <CardHeader>
              <div><CardTitle>Camera view</CardTitle><CardDescription>Privacy masks are applied to this preview.</CardDescription></div>
              <div className="w-56">
                <label className="sr-only" htmlFor="z-cam">Camera</label>
                <Select id="z-cam" value={cameraId} onChange={(e) => { setCameraId(e.target.value); setD(blank()); }}>
                  {cameras.data.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {cameraId ? (
                <PolygonEditor
                  imageUrl={p(`/cameras/${cameraId}/snapshot`)}
                  mode={d.kind}
                  draft={d.points}
                  onDraftChange={(points) => setD({ ...d, points })}
                  disabled={!editable}
                  shapes={(zones.data ?? []).filter((z) => z.id !== d.id).map((z) => ({ id: z.id, points: z.points, kind: z.kind, label: z.name }))}
                />
              ) : null}
              <div className="mt-4 space-y-2">
                {(zones.data ?? []).map((z) => (
                  <div key={z.id} className="flex flex-col gap-1 rounded-md border border-line bg-surface-2 px-3 py-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-medium">{z.name}
                        <Badge tone={z.kind === "line" ? "review" : "teal"}>{z.kind === "line" ? "Entrance boundary" : "Restricted area"}</Badge>
                        {!z.enabled ? <Badge tone="muted">disabled</Badge> : null}
                      </div>
                      <div className="text-[11px] text-ink-faint">Monitored: {describeWindows(z.monitoring_schedule)} · Approved access: {z.approved_access.length ? describeWindows(z.approved_access) : "none"}</div>
                    </div>
                    {editable ? (
                      <div className="flex gap-1">
                        <Button size="icon" variant="ghost" aria-label={`Edit ${z.name}`} onClick={() => setD({ id: z.id, name: z.name, kind: z.kind, points: z.points, direction: z.direction, monitoring_schedule: z.monitoring_schedule, approved_access: z.approved_access, enabled: z.enabled, quickRule: false })}><Pencil /></Button>
                        <Button size="icon" variant="ghost" aria-label={`Delete ${z.name}`} onClick={() => remove(z)}><Trash2 /></Button>
                      </div>
                    ) : null}
                  </div>
                ))}
                {zones.data && !zones.data.length ? <p className="text-xs text-ink-faint">No zones on this camera yet.</p> : null}
              </div>
            </CardContent>
          </Card>
          {editable ? (
            <Card className="lg:col-span-2">
              <CardHeader><div><CardTitle>{d.id ? "Edit zone" : "New zone"}</CardTitle><CardDescription>Draw on the camera view, then save.</CardDescription></div></CardHeader>
              <CardContent>
                <form onSubmit={save} className="space-y-4">
                  <Field label="Zone name" htmlFor="z-name">
                    <Input id="z-name" list="zone-examples" required value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} />
                    <datalist id="zone-examples">{EXAMPLES.map((x) => <option key={x} value={x} />)}</datalist>
                  </Field>
                  {!d.id ? (
                    <Field label="Type" htmlFor="z-kind">
                      <Select id="z-kind" value={d.kind} onChange={(e) => setD({ ...d, kind: e.target.value as Draft["kind"], points: [] })}>
                        <option value="area">Restricted area (polygon)</option>
                        <option value="line">Entrance boundary (line)</option>
                      </Select>
                    </Field>
                  ) : null}
                  {d.kind === "line" ? (
                    <Field label="Crossing direction" htmlFor="z-dir" hint="A→B is the order you clicked the two points.">
                      <Select id="z-dir" value={d.direction} onChange={(e) => setD({ ...d, direction: e.target.value as Draft["direction"] })}>
                        <option value="any">Either direction</option>
                        <option value="a_to_b">Left of A→B to right</option>
                        <option value="b_to_a">Right of A→B to left</option>
                      </Select>
                    </Field>
                  ) : null}
                  <div>
                    <div className="mb-1.5 text-xs font-medium text-ink-muted">Monitoring hours</div>
                    <ScheduleEditor idPrefix="mon" value={d.monitoring_schedule} onChange={(w) => setD({ ...d, monitoring_schedule: w })} emptyLabel="Monitored at all times" />
                  </div>
                  <div>
                    <div className="mb-1.5 text-xs font-medium text-ink-muted">Approved access periods (entries are logged, no incident)</div>
                    <ScheduleEditor idPrefix="acc" value={d.approved_access} onChange={(w) => setD({ ...d, approved_access: w })} emptyLabel="No approved access periods" />
                  </div>
                  <Checkbox checked={d.enabled} onChange={(e) => setD({ ...d, enabled: e.target.checked })} label="Zone enabled" />
                  {!d.id ? <Checkbox checked={d.quickRule} onChange={(e) => setD({ ...d, quickRule: e.target.checked })} label="Also create an after-hours rule (18:00–06:00, Review Required, email org admins & site managers)" /> : null}
                  <Callout>
                    Access-control integration (badge readers) is a future interface. Until then, camera detections are treated as
                    evidence for human review only.
                  </Callout>
                  <ErrorText error={error} />
                  {saved ? <p className="text-xs text-teal" role="status">{saved}</p> : null}
                  <div className="flex gap-2">
                    <Button type="submit" disabled={d.points.length < minPts || !d.name}>{d.id ? "Save changes" : "Save zone"}</Button>
                    {d.id ? <Button type="button" variant="ghost" onClick={() => setD(blank())}>Cancel</Button> : null}
                  </div>
                </form>
              </CardContent>
            </Card>
          ) : null}
        </div>
      )}
    </>
  );
}
