"use client";

import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, Callout, Empty, ErrorText, PageHeader, Spinner, Stat, StatusBadge } from "@/components/ui/misc";
import { EVENT_LABEL, SEVERITY_LABEL, fmtRelative, fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Severity } from "@/lib/types";

interface Overview {
  cameras: { total: number; online: number; offline: number; degraded: number; unknown: number;
    items: { id: string; name: string; status: string; source_type: string; last_seen_at: string | null }[] };
  zones: number;
  active_incidents: number;
  active_by_severity: Partial<Record<Severity, number>>;
  incident_trend: { date: string; count: number }[];
  recent_events: { id: string; event_type: string; occurred_at: string; confidence: number | null; simulated: boolean; rule_outcome: string }[];
  edge_agents: { id: string; name: string; last_seen_at: string | null }[];
  privacy: { surveillance_notice_confirmed: boolean; weapon_detection_mode: string; face_covering_mode: string };
}

function TrendChart({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div>
      <div className="flex h-32 items-end gap-1.5" role="img" aria-label={`Incidents per day, last ${data.length} days`}>
        {data.map((d) => (
          <div key={d.date} className="group relative flex-1">
            <div
              className="w-full rounded-sm bg-teal/70 group-hover:bg-teal"
              style={{ height: `${Math.max(2, (d.count / max) * 120)}px`, opacity: d.count ? 1 : 0.25 }}
            />
            <span className="pointer-events-none absolute -top-6 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-surface-3 px-1.5 py-0.5 text-[10px] group-hover:block">
              {d.date.slice(5)}: {d.count}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-ink-faint">
        <span>{data[0]?.date.slice(5)}</span>
        <span>{data[data.length - 1]?.date.slice(5)}</span>
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const { p, siteId, org } = useOrg();
  const { data, error } = useData<Overview>(p(`/overview${siteId ? `?site_id=${siteId}` : ""}`), { poll: 15000 });
  if (error) return <ErrorText error={error} />;
  if (!data) return <Spinner />;
  const sev = data.active_by_severity;
  return (
    <>
      <PageHeader title="Overview" description="Live status of cameras, monitored zones and potential incidents awaiting human review." />
      {!data.privacy.surveillance_notice_confirmed ? (
        <Callout tone="warn" title="Surveillance notice not yet confirmed" className="mb-5">
          Before monitoring live cameras, confirm that required workplace / school surveillance notices are in place
          (Settings → Privacy). Obligations vary by state — see the compliance checklist.
        </Callout>
      ) : null}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Cameras online" value={`${data.cameras.online}/${data.cameras.total}`} sub={`${data.cameras.offline} offline · ${data.cameras.unknown} not reporting`} tone="teal" />
        <Stat label="Monitored zones" value={data.zones} />
        <Stat label="Active alerts" value={data.active_incidents} tone={data.active_incidents ? "critical" : undefined}
          sub={(["critical_review", "high_priority", "review_required", "informational"] as Severity[])
            .filter((s) => sev[s]).map((s) => `${sev[s]} ${SEVERITY_LABEL[s]}`).join(" · ") || "Nothing awaiting review"} />
        <Stat label="Edge agents" value={data.edge_agents.length} sub={data.edge_agents[0] ? `last seen ${fmtRelative(data.edge_agents[0].last_seen_at)}` : "none registered"} />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Alert trend</CardTitle>
              <CardDescription>Potential incidents created per day (14 days)</CardDescription>
            </div>
            <Link href="/incidents" className="text-xs text-teal hover:underline">Incident Centre →</Link>
          </CardHeader>
          <CardContent><TrendChart data={data.incident_trend} /></CardContent>
        </Card>
        <Card>
          <CardHeader><div><CardTitle>Camera health</CardTitle><CardDescription>Reported by edge agents / uploads</CardDescription></div></CardHeader>
          <CardContent className="space-y-2">
            {data.cameras.items.length ? data.cameras.items.slice(0, 8).map((c) => (
              <div key={c.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate">{c.name}</span>
                <span className="flex items-center gap-2 text-[11px] text-ink-faint">
                  {c.source_type === "upload" ? "uploads" : fmtRelative(c.last_seen_at)}
                  <StatusBadge status={c.source_type === "upload" ? "staged" : c.status} />
                </span>
              </div>
            )) : <Empty title="No cameras yet"><Link className="text-teal" href="/cameras">Add a camera</Link></Empty>}
          </CardContent>
        </Card>
      </div>
      <Card className="mt-5">
        <CardHeader><div><CardTitle>Recent detection events</CardTitle><CardDescription>Observations from AI models — not conclusions.</CardDescription></div></CardHeader>
        <CardContent>
          {data.recent_events.length ? (
            <ul className="divide-y divide-line/60">
              {data.recent_events.map((e) => (
                <li key={e.id} className="flex flex-col gap-1 py-2 text-sm sm:flex-row sm:items-center sm:justify-between">
                  <span className="flex items-center gap-2">
                    {EVENT_LABEL[e.event_type] ?? e.event_type}
                    {e.simulated ? <Badge tone="review">SIMULATED</Badge> : null}
                    {e.confidence !== null ? <span className="text-xs text-ink-faint tabular">conf {e.confidence.toFixed(2)}</span> : null}
                  </span>
                  <span className="text-xs text-ink-faint">{fmtTime(e.occurred_at, org.timezone)} · {e.rule_outcome || "—"}</span>
                </li>
              ))}
            </ul>
          ) : <Empty title="No events yet">Upload a staged video in Video Analysis or connect an edge agent.</Empty>}
        </CardContent>
      </Card>
    </>
  );
}
