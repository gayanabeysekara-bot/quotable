"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { ScheduleEditor } from "@/components/schedule-editor";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form";
import { Badge, Callout, Dialog, Empty, ErrorText, PageHeader, SeverityBadge, Spinner, Table, Td, Th } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { EVENT_LABEL, SEVERITY_LABEL, describeWindows } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Camera, Member, Rule, Severity, Zone } from "@/lib/types";

const TYPES = ["zone_entry", "line_crossing", "weapon_possible", "face_covering_observed", "camera_offline", "camera_obstructed"];

function RuleDialog({ rule, onClose, onSaved }: { rule: Rule | null; onClose: () => void; onSaved: () => void }) {
  const { p, sites } = useOrg();
  const cameras = useData<Camera[]>(p("/cameras"));
  const zones = useData<Zone[]>(p("/zones"));
  const members = useData<Member[]>(p("/members"));
  const [r, setR] = useState<Omit<Rule, "id">>(() => rule ?? {
    name: "", event_type: "zone_entry", site_id: null, camera_id: null, zone_id: null,
    schedule: [{ days: [0, 1, 2, 3, 4, 5, 6], start: "18:00", end: "06:00" }], severity: "review_required",
    min_confidence: 0.4, suppression_seconds: 300, notify_email: true, recipient_user_ids: [], enabled: true,
  });
  const [error, setError] = useState<unknown>(null);
  const set = <K extends keyof typeof r>(k: K, v: (typeof r)[K]) => setR((x) => ({ ...x, [k]: v }));
  const face = r.event_type === "face_covering_observed";

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (rule) {
        const { name, schedule, severity, min_confidence, suppression_seconds, notify_email, recipient_user_ids, enabled } = r;
        await api(p(`/rules/${rule.id}`), { method: "PATCH", body: { name, schedule, severity, min_confidence, suppression_seconds, notify_email, recipient_user_ids, enabled } });
      } else {
        await api(p("/rules"), { body: r });
      }
      onSaved();
    } catch (err) {
      setError(err);
    }
  };

  const camOpts = (cameras.data ?? []).filter((c) => !r.site_id || c.site_id === r.site_id);
  const zoneOpts = (zones.data ?? []).filter((z) => (!r.camera_id || z.camera_id === r.camera_id) && (r.event_type === "line_crossing" ? z.kind === "line" : z.kind === "area"));
  return (
    <Dialog open onClose={onClose} title={rule ? `Edit rule` : "New rule"} wide>
      <form onSubmit={save} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Rule name" htmlFor="r-name"><Input id="r-name" required value={r.name} placeholder="Finance Office after hours" onChange={(e) => set("name", e.target.value)} /></Field>
          <Field label="Event category" htmlFor="r-type">
            <Select id="r-type" value={r.event_type} disabled={!!rule} onChange={(e) => set("event_type", e.target.value)}>
              {TYPES.map((t) => <option key={t} value={t}>{EVENT_LABEL[t]}</option>)}
            </Select>
          </Field>
          <Field label="Site" htmlFor="r-site">
            <Select id="r-site" value={r.site_id ?? ""} disabled={!!rule} onChange={(e) => setR({ ...r, site_id: e.target.value || null, camera_id: null, zone_id: null })}>
              <option value="">All sites</option>{sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Select>
          </Field>
          <Field label="Camera" htmlFor="r-cam">
            <Select id="r-cam" value={r.camera_id ?? ""} disabled={!!rule} onChange={(e) => setR({ ...r, camera_id: e.target.value || null, zone_id: null })}>
              <option value="">Any camera</option>{camOpts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Field>
          {r.event_type === "zone_entry" || r.event_type === "line_crossing" ? (
            <Field label="Zone" htmlFor="r-zone">
              <Select id="r-zone" value={r.zone_id ?? ""} disabled={!!rule} onChange={(e) => set("zone_id", e.target.value || null)}>
                <option value="">Any zone</option>{zoneOpts.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}
              </Select>
            </Field>
          ) : <div />}
          <Field label="Severity" htmlFor="r-sev" hint={face ? "Face-covering observations are neutral and capped at Informational." : "Critical Review = request for urgent human review, not confirmation of a threat."}>
            <Select id="r-sev" value={face ? "informational" : r.severity} disabled={face} onChange={(e) => set("severity", e.target.value as Severity)}>
              {(Object.keys(SEVERITY_LABEL) as Severity[]).map((s) => <option key={s} value={s}>{SEVERITY_LABEL[s]}</option>)}
            </Select>
          </Field>
          <Field label="Minimum model confidence" htmlFor="r-conf"><Input id="r-conf" type="number" min={0} max={1} step={0.05} value={r.min_confidence} onChange={(e) => set("min_confidence", Number(e.target.value))} /></Field>
          <Field label="Suppress repeats for (seconds)" htmlFor="r-supp" hint="Repeat events within this window are folded into the open incident."><Input id="r-supp" type="number" min={0} max={86400} value={r.suppression_seconds} onChange={(e) => set("suppression_seconds", Number(e.target.value))} /></Field>
        </div>
        <div>
          <div className="mb-1.5 text-xs font-medium text-ink-muted">Active schedule (site local time)</div>
          <ScheduleEditor idPrefix="rs" value={r.schedule} onChange={(w) => set("schedule", w)} emptyLabel="Active at all times" />
        </div>
        <div>
          <div className="mb-1.5 text-xs font-medium text-ink-muted">Notification recipients (email)</div>
          <Checkbox checked={r.notify_email} onChange={(e) => set("notify_email", e.target.checked)} label="Send email notifications (no images are included)" />
          {r.notify_email ? (
            <div className="mt-2 grid gap-1 sm:grid-cols-2">
              {(members.data ?? []).map((m) => (
                <Checkbox key={m.user_id} checked={r.recipient_user_ids.includes(m.user_id)}
                  onChange={(e) => set("recipient_user_ids", e.target.checked ? [...r.recipient_user_ids, m.user_id] : r.recipient_user_ids.filter((x) => x !== m.user_id))}
                  label={<span className="text-xs">{m.full_name || m.email} <span className="text-ink-faint">({m.role.replace("_", " ")})</span></span>} />
              ))}
              <p className="text-[11px] text-ink-faint sm:col-span-2">If none are selected, all organisation admins and site managers are notified.</p>
            </div>
          ) : null}
        </div>
        <Checkbox checked={r.enabled} onChange={(e) => set("enabled", e.target.checked)} label="Rule enabled" />
        <ErrorText error={error} />
        <div className="flex justify-end gap-2"><Button type="button" variant="ghost" onClick={onClose}>Cancel</Button><Button type="submit">Save rule</Button></div>
      </form>
    </Dialog>
  );
}

export default function RulesPage() {
  const { p, can } = useOrg();
  const { data, error, reload } = useData<Rule[]>(p("/rules"));
  const zones = useData<Zone[]>(p("/zones"));
  const [editing, setEditing] = useState<Rule | "new" | null>(null);
  const zoneName = (id: string | null) => (id ? zones.data?.find((z) => z.id === id)?.name ?? "—" : "Any");
  const remove = async (r: Rule) => {
    if (!confirm(`Delete rule "${r.name}"?`)) return;
    await api(p(`/rules/${r.id}`), { method: "DELETE" });
    reload();
  };
  return (
    <>
      <PageHeader title="Rules & Notifications" description="When a detection event matches a rule — category, place, time and confidence — a potential incident is created and recipients are emailed."
        actions={can("manage_zones_rules") ? <Button onClick={() => setEditing("new")}><Plus /> New rule</Button> : null} />
      <Callout className="mb-4" title="Human in the loop">Rules only create incidents and send notifications. They never call emergency services, lock doors or take other automatic action. Push and SMS channels are planned interfaces, not yet available.</Callout>
      <ErrorText error={error} />
      <Card>
        <CardContent className="p-0">
          {!data ? <div className="p-5"><Spinner /></div> : !data.length ? <div className="p-5"><Empty title="No rules yet">Create one here, or tick “also create an after-hours rule” when drawing a zone.</Empty></div> : (
            <Table>
              <thead><tr><Th>Rule</Th><Th>Category</Th><Th>Zone</Th><Th>Schedule</Th><Th>Severity</Th><Th>Suppression</Th><Th /></tr></thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.id}>
                    <Td><div className="font-medium">{r.name}</div>{!r.enabled ? <Badge tone="muted">disabled</Badge> : null}</Td>
                    <Td className="text-xs">{EVENT_LABEL[r.event_type] ?? r.event_type}</Td>
                    <Td className="text-xs text-ink-muted">{zoneName(r.zone_id)}</Td>
                    <Td className="text-xs text-ink-muted">{describeWindows(r.schedule)}</Td>
                    <Td><SeverityBadge severity={r.severity} /></Td>
                    <Td className="tabular text-xs">{r.suppression_seconds}s · ≥{r.min_confidence}</Td>
                    <Td className="text-right">{can("manage_zones_rules") ? (
                      <div className="flex justify-end gap-1">
                        <Button size="icon" variant="ghost" aria-label={`Edit ${r.name}`} onClick={() => setEditing(r)}><Pencil /></Button>
                        <Button size="icon" variant="ghost" aria-label={`Delete ${r.name}`} onClick={() => remove(r)}><Trash2 /></Button>
                      </div>) : null}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
      {editing ? <RuleDialog rule={editing === "new" ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} /> : null}
    </>
  );
}
