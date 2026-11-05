"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { PolygonEditor } from "@/components/polygon-editor";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/form";
import { Badge, Callout, Dialog, Empty, ErrorText, PageHeader, Spinner, StatusBadge, Table, Td, Th } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { fmtRelative } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Camera, Point } from "@/lib/types";

interface EdgeAgentRow { id: string; site_id: string; name: string; revoked_at: string | null }

type Form = {
  site_id: string; name: string; location_label: string; source_type: "rtsp" | "onvif" | "upload";
  stream_url: string; onvif_xaddr: string; username: string; password: string; edge_agent_id: string;
  privacy_masks: Point[][]; clear_credentials: boolean;
};

function CameraDialog({ camera, onClose, onSaved }: { camera: Camera | null; onClose: () => void; onSaved: () => void }) {
  const { p, sites, siteId } = useOrg();
  const agents = useData<EdgeAgentRow[]>(p("/edge-agents"));
  const [f, setF] = useState<Form>(() => ({
    site_id: camera?.site_id || siteId || sites[0]?.id || "",
    name: camera?.name ?? "", location_label: camera?.location_label ?? "",
    source_type: camera?.source_type ?? "upload", stream_url: camera?.stream_url ?? "", onvif_xaddr: camera?.onvif_xaddr ?? "",
    username: "", password: "", edge_agent_id: camera?.edge_agent_id ?? "", privacy_masks: camera?.privacy_masks ?? [],
    clear_credentials: false,
  }));
  const [draft, setDraft] = useState<Point[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => ({ ...x, [k]: v }));

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body: Record<string, unknown> = {
      name: f.name, location_label: f.location_label, stream_url: f.stream_url, onvif_xaddr: f.onvif_xaddr,
      edge_agent_id: f.edge_agent_id || null, privacy_masks: f.privacy_masks,
    };
    if (f.username) body.username = f.username;
    if (f.password) body.password = f.password;
    try {
      if (camera) {
        if (f.clear_credentials) body.clear_credentials = true;
        await api(p(`/cameras/${camera.id}`), { method: "PATCH", body });
      } else {
        await api(p("/cameras"), { body: { ...body, site_id: f.site_id, source_type: f.source_type } });
      }
      onSaved();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const live = f.source_type !== "upload";
  return (
    <Dialog open onClose={onClose} title={camera ? `Edit ${camera.name}` : "Add camera"} wide>
      <form onSubmit={save} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Site" htmlFor="c-site">
            <Select id="c-site" value={f.site_id} disabled={!!camera} onChange={(e) => set("site_id", e.target.value)} required>
              <option value="" disabled>Select a site</option>
              {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Select>
          </Field>
          <Field label="Source" htmlFor="c-src">
            <Select id="c-src" value={f.source_type} disabled={!!camera} onChange={(e) => set("source_type", e.target.value as Form["source_type"])}>
              <option value="upload">Uploaded staged video</option>
              <option value="rtsp">RTSP stream (via edge agent)</option>
              <option value="onvif">ONVIF camera (via edge agent)</option>
            </Select>
          </Field>
          <Field label="Camera name" htmlFor="c-name"><Input id="c-name" required value={f.name} onChange={(e) => set("name", e.target.value)} /></Field>
          <Field label="Location" htmlFor="c-loc"><Input id="c-loc" placeholder="e.g. Admin corridor, level 1" value={f.location_label} onChange={(e) => set("location_label", e.target.value)} /></Field>
        </div>
        {live ? (
          <>
            <Callout title="Read-only access">
              Create a dedicated view-only user on the camera/NVR. Credentials are encrypted at rest, sent only to the
              edge agent for this site, and never shown again in the browser. Do not put credentials in the URL.
            </Callout>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="RTSP stream URL" htmlFor="c-url" hint="e.g. rtsp://192.168.1.20:554/Streaming/Channels/101">
                <Input id="c-url" value={f.stream_url} onChange={(e) => set("stream_url", e.target.value)} />
              </Field>
              {f.source_type === "onvif" ? (
                <Field label="ONVIF device service" htmlFor="c-onvif" hint="From edge discovery (zoneguard-edge discover)">
                  <Input id="c-onvif" value={f.onvif_xaddr} onChange={(e) => set("onvif_xaddr", e.target.value)} />
                </Field>
              ) : <div />}
              <Field label="Username (write-only)" htmlFor="c-user"><Input id="c-user" autoComplete="off" value={f.username} placeholder={camera?.has_credentials ? "•••••• (stored)" : ""} onChange={(e) => set("username", e.target.value)} /></Field>
              <Field label="Password (write-only)" htmlFor="c-pass"><Input id="c-pass" type="password" autoComplete="new-password" value={f.password} placeholder={camera?.has_credentials ? "•••••• (stored)" : ""} onChange={(e) => set("password", e.target.value)} /></Field>
              <Field label="Edge agent" htmlFor="c-edge">
                <Select id="c-edge" value={f.edge_agent_id} onChange={(e) => set("edge_agent_id", e.target.value)}>
                  <option value="">Any agent at this site</option>
                  {(agents.data ?? []).filter((a) => a.site_id === f.site_id && !a.revoked_at).map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </Select>
              </Field>
              {camera?.has_credentials ? (
                <label className="mt-6 flex items-center gap-2 text-sm"><input type="checkbox" className="accent-[#2DD4BF]" checked={f.clear_credentials} onChange={(e) => set("clear_credentials", e.target.checked)} /> Remove stored credentials</label>
              ) : null}
            </div>
          </>
        ) : null}
        <div>
          <div className="mb-2 text-xs font-medium text-ink-muted">Privacy masks — areas blacked out before any detection, preview or storage (e.g. windows into neighbouring property, toilets, change rooms).</div>
          <PolygonEditor
            imageUrl={camera ? p(`/cameras/${camera.id}/snapshot`) : null}
            mode="mask"
            draft={draft}
            onDraftChange={setDraft}
            shapes={f.privacy_masks.map((m, i) => ({ id: `m${i}`, points: m, kind: "mask" as const, label: `Mask ${i + 1}` }))}
          />
          <div className="mt-2 flex flex-wrap gap-2">
            <Button type="button" size="sm" variant="secondary" disabled={draft.length < 3}
              onClick={() => { set("privacy_masks", [...f.privacy_masks, draft]); setDraft([]); }}>Add mask</Button>
            {f.privacy_masks.map((_, i) => (
              <Button key={i} type="button" size="sm" variant="ghost" onClick={() => set("privacy_masks", f.privacy_masks.filter((__, j) => j !== i))}>
                <Trash2 /> Mask {i + 1}
              </Button>
            ))}
          </div>
        </div>
        <ErrorText error={error} />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save camera"}</Button>
        </div>
      </form>
    </Dialog>
  );
}

export default function CamerasPage() {
  const { p, siteId, sites, can } = useOrg();
  const { data, error, reload } = useData<Camera[]>(p(`/cameras${siteId ? `?site_id=${siteId}` : ""}`), { poll: 20000 });
  const [editing, setEditing] = useState<Camera | null | "new">(null);
  const siteName = (id: string) => sites.find((s) => s.id === id)?.name ?? "—";

  const remove = async (c: Camera) => {
    if (!confirm(`Delete camera "${c.name}"? Its zones, rules, uploaded videos and events will be removed.`)) return;
    await api(p(`/cameras/${c.id}`), { method: "DELETE" });
    reload();
  };

  return (
    <>
      <PageHeader
        title="Camera Management"
        description="Existing IP cameras (RTSP/ONVIF) connect through the on-premises edge agent; video stays on your network. Upload cameras hold staged footage for analysis."
        actions={can("manage_cameras") ? (
          <Button onClick={() => setEditing("new")} disabled={!sites.length} title={!sites.length ? "Create a site first (Settings → Sites)" : undefined}>
            <Plus /> Add camera
          </Button>
        ) : null}
      />
      {!sites.length ? <Callout tone="warn" className="mb-4">Create a site first in Settings → Sites.</Callout> : null}
      <ErrorText error={error} />
      <Card>
        <CardContent className="p-0">
          {!data ? <div className="p-5"><Spinner /></div> : data.length === 0 ? <div className="p-5"><Empty title="No cameras">Add an upload camera to analyse staged footage, or an RTSP camera served by an edge agent.</Empty></div> : (
            <Table>
              <thead><tr><Th>Camera</Th><Th>Site</Th><Th>Source</Th><Th>Status</Th><Th>Health</Th><Th>Privacy</Th><Th /></tr></thead>
              <tbody>
                {data.map((c) => (
                  <tr key={c.id}>
                    <Td><div className="font-medium">{c.name}</div><div className="text-xs text-ink-faint">{c.location_label}</div></Td>
                    <Td className="text-ink-muted">{siteName(c.site_id)}</Td>
                    <Td><Badge tone="muted">{c.source_type.toUpperCase()}</Badge>{c.has_credentials ? <span className="ml-1 text-[11px] text-ink-faint">creds stored</span> : null}</Td>
                    <Td>{c.source_type === "upload" ? <Badge tone="muted">staged uploads</Badge> : <StatusBadge status={c.status} />}</Td>
                    <Td className="text-xs text-ink-muted">
                      {c.source_type === "upload" ? "—" : (
                        <>
                          <div>seen {fmtRelative(c.last_seen_at)}</div>
                          {c.health?.fps ? <div className="tabular">{String(c.health.fps)} fps · {String(c.health.reconnects ?? 0)} reconnects</div> : null}
                          {c.last_error ? <div className="text-sev-high">{c.last_error}</div> : null}
                        </>
                      )}
                    </Td>
                    <Td className="text-xs text-ink-muted">{c.privacy_masks.length ? `${c.privacy_masks.length} mask(s)` : "none"}</Td>
                    <Td className="text-right">
                      {can("manage_cameras") ? (
                        <div className="flex justify-end gap-1">
                          <Button size="icon" variant="ghost" aria-label={`Edit ${c.name}`} onClick={() => setEditing(c)}><Pencil /></Button>
                          <Button size="icon" variant="ghost" aria-label={`Delete ${c.name}`} onClick={() => remove(c)}><Trash2 /></Button>
                        </div>
                      ) : null}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
      {editing ? <CameraDialog camera={editing === "new" ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} /> : null}
    </>
  );
}
