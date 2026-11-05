"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Callout, Empty, ErrorText, PageHeader, Spinner, Stat, Table, Td, Th } from "@/components/ui/misc";
import { fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";

interface Metrics {
  window_days: number; incidents: number; reviewed: number; dismissed_false_positive: number;
  reviewer_precision: number | null; false_alerts_per_camera_per_day: number | null;
  per_category: Record<string, { incidents: number; dismissed_false_positive: number; confirmed_relevant: number }>;
  notifications: { sent: number; failed: number; p50_latency_ms: number | null; p95_latency_ms: number | null };
  camera_reconnects: { attempts: number; successes: number; success_rate: number | null };
  note: string;
}
interface Run { id: string; name: string; detector_task: string; model_name: string; model_version: string; dataset_label: string; metrics: Record<string, unknown>; created_at: string }

const n = (v: unknown, digits = 3) => (typeof v === "number" ? v.toFixed(digits) : "—");

export default function EvaluationPage() {
  const { p } = useOrg();
  const m = useData<Metrics>(p("/metrics?days=30"));
  const runs = useData<Run[]>(p("/evaluations"));
  return (
    <>
      <PageHeader title="Detector Evaluation" description="Measured performance only. Nothing on this page is an estimate or vendor claim." />
      <Callout tone="warn" className="mb-5" title="Not validated for safety-critical use">
        Accuracy depends on camera placement, lighting and footage. Run the evaluation framework on your own staged, consented footage
        with ground-truth annotations before relying on any detector, and obtain independent validation before any safety-critical use.
      </Callout>
      <h2 className="mb-3 text-sm font-semibold">Operational metrics (last 30 days, from real review outcomes)</h2>
      <ErrorText error={m.error} />
      {!m.data ? <Spinner /> : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Reviewer-confirmed precision" value={m.data.reviewer_precision === null ? "—" : n(m.data.reviewer_precision, 2)} sub={`${m.data.reviewed} reviewed / ${m.data.incidents} incidents`} />
            <Stat label="False alerts / camera / day" value={m.data.false_alerts_per_camera_per_day === null ? "—" : n(m.data.false_alerts_per_camera_per_day, 3)} sub={`${m.data.dismissed_false_positive} dismissed as false positive`} />
            <Stat label="Alert delivery latency" value={m.data.notifications.p50_latency_ms === null ? "—" : `${Math.round(m.data.notifications.p50_latency_ms)} ms`} sub={`p95 ${m.data.notifications.p95_latency_ms === null ? "—" : Math.round(m.data.notifications.p95_latency_ms) + " ms"} · ${m.data.notifications.failed} failed`} />
            <Stat label="Camera reconnect success" value={m.data.camera_reconnects.success_rate === null ? "—" : `${Math.round(m.data.camera_reconnects.success_rate * 100)}%`} sub={`${m.data.camera_reconnects.successes}/${m.data.camera_reconnects.attempts} attempts`} />
          </div>
          <p className="mt-2 text-xs text-ink-faint">{m.data.note}</p>
        </>
      )}
      <Card className="mt-6">
        <CardHeader><div><CardTitle>Ground-truth evaluation runs</CardTitle><CardDescription>Produced by <code>python -m evaluation.run</code> against annotated footage and submitted here.</CardDescription></div></CardHeader>
        <CardContent className="p-0">
          {!runs.data ? <div className="p-5"><Spinner /></div> : !runs.data.length ? (
            <div className="p-5"><Empty title="No evaluation runs submitted">See evaluation/README.md for how to annotate staged footage and run the evaluator.</Empty></div>
          ) : (
            <Table>
              <thead><tr><Th>Run</Th><Th>Model</Th><Th>Precision</Th><Th>Recall</Th><Th>FP</Th><Th>FN</Th><Th>Latency p50</Th><Th>Date</Th></tr></thead>
              <tbody>
                {runs.data.map((r) => (
                  <tr key={r.id}>
                    <Td><div className="font-medium">{r.name}</div><div className="text-[11px] text-ink-faint">{r.dataset_label} · {r.detector_task}</div></Td>
                    <Td className="text-xs">{r.model_version || r.model_name}</Td>
                    <Td className="tabular">{n(r.metrics.precision)}</Td>
                    <Td className="tabular">{n(r.metrics.recall)}</Td>
                    <Td className="tabular">{String(r.metrics.false_positives ?? "—")}</Td>
                    <Td className="tabular">{String(r.metrics.false_negatives ?? "—")}</Td>
                    <Td className="tabular text-xs">{r.metrics.latency_ms_p50 !== undefined ? `${n(r.metrics.latency_ms_p50, 1)} ms` : "—"}</Td>
                    <Td className="text-xs text-ink-muted">{fmtTime(r.created_at)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
