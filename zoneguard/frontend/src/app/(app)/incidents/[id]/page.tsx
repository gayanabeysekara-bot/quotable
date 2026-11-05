"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Select, Textarea } from "@/components/ui/form";
import { Badge, Callout, ErrorText, SeverityBadge, Spinner, StatusBadge } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { EVENT_LABEL, fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { EventRow, Incident, Member } from "@/lib/types";

interface Detail {
  incident: Incident;
  history: { id: string; actor_label: string; action: string; from_status: string | null; to_status: string | null; note: string; created_at: string }[];
  notifications: { id: string; channel: string; recipient: string; status: string; error: string; sent_at: string | null; latency_ms: number | null }[];
  event: EventRow | null;
  disclaimer: string;
}

const ACTIONS: Record<string, { action: string; label: string; variant?: "default" | "secondary" | "danger" | "outline" }[]> = {
  open: [{ action: "acknowledge", label: "Acknowledge" }, { action: "escalate", label: "Escalate", variant: "secondary" }, { action: "dismiss", label: "Dismiss", variant: "outline" }],
  acknowledged: [{ action: "escalate", label: "Escalate", variant: "secondary" }, { action: "close", label: "Close" }, { action: "dismiss", label: "Dismiss", variant: "outline" }],
  escalated: [{ action: "acknowledge", label: "Acknowledge" }, { action: "close", label: "Close" }, { action: "dismiss", label: "Dismiss", variant: "outline" }],
  dismissed: [{ action: "reopen", label: "Reopen", variant: "outline" }],
  closed: [{ action: "reopen", label: "Reopen", variant: "outline" }],
};
const DISMISS = [["false_positive", "False positive (detector error)"], ["authorised_access", "Authorised access"], ["test_or_staged", "Test / staged footage"], ["duplicate", "Duplicate"], ["other", "Other"]];
const CLOSE = [["resolved", "Resolved"], ["no_further_action", "No further action"], ["referred_externally", "Referred externally (by a person)"], ["other", "Other"]];

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { p, can, org } = useOrg();
  const { data, error, reload } = useData<Detail>(p(`/incidents/${id}`));
  const members = useData<Member[]>(p("/members"));
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);

  if (error) return <ErrorText error={error} />;
  if (!data) return <Spinner />;
  const i = data.incident;
  const reviewer = can("review_incidents");

  const act = async (action: string) => {
    if ((action === "dismiss" || action === "close") && pending !== action) {
      setPending(action);
      setReason(action === "dismiss" ? "" : "resolved");
      return;
    }
    setActionError(null);
    try {
      await api(p(`/incidents/${id}/actions`), { body: { action, note, reason } });
      setNote("");
      setPending(null);
      reload();
    } catch (e) {
      setActionError(e);
    }
  };
  const addNote = async () => {
    try {
      await api(p(`/incidents/${id}/notes`), { body: { note } });
      setNote("");
      reload();
    } catch (e) {
      setActionError(e);
    }
  };
  const assign = async (userId: string) => {
    await api(p(`/incidents/${id}/assign`), { body: { user_id: userId || null } });
    reload();
  };

  return (
    <>
      <Link href="/incidents" className="mb-4 inline-flex items-center gap-1 text-xs text-ink-muted hover:text-ink"><ArrowLeft className="h-3.5 w-3.5" /> Incident Centre</Link>
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="font-mono text-xs text-ink-faint">{i.reference}</div>
          <h1 className="text-xl font-semibold">{i.title}</h1>
          <div className="mt-2 flex flex-wrap gap-2"><SeverityBadge severity={i.severity} /><StatusBadge status={i.status} />{i.simulated ? <Badge tone="review">SIMULATED detector</Badge> : null}</div>
        </div>
      </div>
      <Callout className="mb-5">{data.disclaimer}</Callout>
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card>
            <CardHeader><CardTitle>Details</CardTitle></CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
                {[
                  ["Organisation", org.name], ["Site", i.site_name], ["Camera", i.camera_name], ["Zone", i.zone_name],
                  ["Event time", fmtTime(i.occurred_at, org.timezone)], ["Detection type", EVENT_LABEL[i.category] ?? i.category],
                  ["Model confidence", i.confidence !== null ? i.confidence.toFixed(3) : "n/a"], ["Model version", `${i.model_name} ${i.model_version}`],
                  ["Rule triggered", i.rule_name], ["Repeat events folded in", String(i.suppressed_count)],
                  ["Resolution", i.resolution_reason || "—"], ["Incident ID", i.id],
                ].map(([k, v]) => (
                  <div key={k}><dt className="text-[11px] uppercase tracking-wider text-ink-faint">{k}</dt><dd className="mt-0.5 break-all">{v || "—"}</dd></div>
                ))}
              </dl>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Audit trail</CardTitle></CardHeader>
            <CardContent>
              <ol className="relative space-y-4 border-l border-line pl-5" data-testid="incident-history">
                {data.history.map((h) => (
                  <li key={h.id} className="text-sm">
                    <span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full bg-teal" aria-hidden />
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium capitalize">{h.action.replace("_", " ")}</span>
                      {h.to_status ? <span className="text-xs text-ink-faint">{h.from_status ?? "—"} → {h.to_status}</span> : null}
                    </div>
                    <div className="text-xs text-ink-faint">{fmtTime(h.created_at, org.timezone)} · {h.actor_label}</div>
                    {h.note ? <p className="mt-1 whitespace-pre-wrap text-xs text-ink-muted">{h.note}</p> : null}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-5">
          {reviewer ? (
            <Card>
              <CardHeader><CardTitle>Review</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <Field label="Assigned reviewer" htmlFor="assign">
                  <Select id="assign" value={i.assigned_to ?? ""} onChange={(e) => assign(e.target.value)}>
                    <option value="">Unassigned</option>
                    {(members.data ?? []).filter((m) => m.role !== "auditor").map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name || m.email}</option>)}
                  </Select>
                </Field>
                <Field label="Note" htmlFor="note"><Textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you check? Who did you contact?" /></Field>
                {pending ? (
                  <Field label={pending === "dismiss" ? "Dismissal reason (required)" : "Closure reason"} htmlFor="reason">
                    <Select id="reason" value={reason} onChange={(e) => setReason(e.target.value)}>
                      <option value="" disabled>Select…</option>
                      {(pending === "dismiss" ? DISMISS : CLOSE).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </Select>
                  </Field>
                ) : null}
                <ErrorText error={actionError} />
                <div className="flex flex-wrap gap-2">
                  {(ACTIONS[i.status] ?? []).map((a) => (
                    <Button key={a.action} variant={pending === a.action ? "default" : a.variant} onClick={() => act(a.action)} disabled={pending === "dismiss" && a.action === "dismiss" && !reason}>
                      {pending === a.action ? `Confirm ${a.label.toLowerCase()}` : a.label}
                    </Button>
                  ))}
                  <Button variant="ghost" onClick={addNote} disabled={!note.trim()}>Add note</Button>
                </div>
              </CardContent>
            </Card>
          ) : <Callout>Your role can view but not review incidents.</Callout>}
          <Card>
            <CardHeader><CardTitle>Notifications</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-xs">
              {data.notifications.length ? data.notifications.map((n) => (
                <div key={n.id} className="flex items-center justify-between gap-2">
                  <span className="truncate">{n.channel}: {n.recipient}</span>
                  <span className="flex items-center gap-2 text-ink-faint">{n.latency_ms !== null ? `${Math.round(n.latency_ms)} ms` : ""}<StatusBadge status={n.status === "sent" ? "completed" : n.status} /></span>
                </div>
              )) : <p className="text-ink-faint">No notifications for this incident.</p>}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
