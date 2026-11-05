"use client";

import { Download } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/form";
import { Badge, Callout, Empty, ErrorText, PageHeader, SeverityBadge, Spinner, StatusBadge, Table, Td, Th } from "@/components/ui/misc";
import { EVENT_LABEL, SEVERITY_LABEL, fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Incident, Severity } from "@/lib/types";

export default function IncidentsPage() {
  const { p, siteId, org } = useOrg();
  const [status, setStatus] = useState("active");
  const [severity, setSeverity] = useState("");
  const [category, setCategory] = useState("");
  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  if (severity) qs.set("severity", severity);
  if (category) qs.set("category", category);
  if (siteId) qs.set("site_id", siteId);
  const { data, error } = useData<Incident[]>(p(`/incidents?${qs}`), { poll: 10000 });

  return (
    <>
      <PageHeader
        title="Incident Centre"
        description="Potential incidents raised by rules. Every action is recorded. A detection never establishes that a person is unauthorised, dangerous or acted wrongfully."
        actions={<Button asChild variant="outline"><a href={p("/incidents/export")}><Download /> Export CSV</a></Button>}
      />
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <label className="sr-only" htmlFor="f-status">Status</label>
        <Select id="f-status" className="w-full sm:w-48" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="active">Active (needs review)</option>
          <option value="">All statuses</option>
          {["open", "acknowledged", "escalated", "dismissed", "closed"].map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <label className="sr-only" htmlFor="f-sev">Severity</label>
        <Select id="f-sev" className="w-full sm:w-44" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {(Object.keys(SEVERITY_LABEL) as Severity[]).map((s) => <option key={s} value={s}>{SEVERITY_LABEL[s]}</option>)}
        </Select>
        <label className="sr-only" htmlFor="f-cat">Category</label>
        <Select id="f-cat" className="w-full sm:w-52" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {Object.entries(EVENT_LABEL).filter(([k]) => k !== "camera_obstruction_cleared").map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </Select>
      </div>
      <ErrorText error={error} />
      <Card>
        <CardContent className="p-0">
          {!data ? <div className="p-5"><Spinner /></div> : !data.length ? <div className="p-5"><Empty title="No incidents match these filters" /></div> : (
            <>
            <ul className="divide-y divide-line sm:hidden">
              {data.map((i) => (
                <li key={i.id}>
                  <Link href={`/incidents/${i.id}`} className="block px-4 py-3 hover:bg-surface-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[11px] text-teal">{i.reference}</span>
                      <StatusBadge status={i.status} />
                    </div>
                    <div className="mt-1 text-sm font-medium">{i.title}</div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-ink-faint">
                      <SeverityBadge severity={i.severity} />
                      {i.simulated ? <Badge tone="review">SIMULATED</Badge> : null}
                      <span>{fmtTime(i.occurred_at, org.timezone)}</span>
                      <span>{[i.site_name, i.camera_name, i.zone_name].filter(Boolean).join(" · ")}</span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
            <Table className="hidden sm:block">
              <thead><tr><Th>Reference</Th><Th>Severity</Th><Th>Incident</Th><Th>Location</Th><Th>Time</Th><Th>Status</Th><Th>Reviewer</Th></tr></thead>
              <tbody>
                {data.map((i) => (
                  <tr key={i.id} className="hover:bg-surface-2">
                    <Td><Link href={`/incidents/${i.id}`} className="font-mono text-xs text-teal hover:underline">{i.reference}</Link></Td>
                    <Td><SeverityBadge severity={i.severity} /></Td>
                    <Td>
                      <Link href={`/incidents/${i.id}`} className="font-medium hover:text-teal">{i.title}</Link>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-ink-faint">
                        {EVENT_LABEL[i.category] ?? i.category}{i.confidence !== null ? ` · conf ${i.confidence.toFixed(2)}` : ""}
                        {i.suppressed_count ? ` · +${i.suppressed_count} repeats` : ""}
                        {i.simulated ? <Badge tone="review">SIMULATED</Badge> : null}
                      </div>
                    </Td>
                    <Td className="text-xs text-ink-muted">{i.site_name}<br />{[i.camera_name, i.zone_name].filter(Boolean).join(" · ")}</Td>
                    <Td className="whitespace-nowrap text-xs text-ink-muted">{fmtTime(i.occurred_at, org.timezone)}</Td>
                    <Td><StatusBadge status={i.status} /></Td>
                    <Td className="text-xs text-ink-muted">{i.assigned_to_email ?? "—"}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            </>
          )}
        </CardContent>
      </Card>
      <Callout className="mt-4">“Critical Review” means urgent human review is requested — it is not confirmation that a threat exists. ZoneGuard never contacts emergency services or changes physical access automatically.</Callout>
    </>
  );
}
