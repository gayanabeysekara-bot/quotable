import type { Severity } from "./types";

export const SEVERITY_LABEL: Record<Severity, string> = {
  informational: "Informational",
  review_required: "Review Required",
  high_priority: "High Priority",
  critical_review: "Critical Review",
};

export const EVENT_LABEL: Record<string, string> = {
  zone_entry: "Restricted-zone entry",
  line_crossing: "Boundary crossing",
  weapon_possible: "Possible visible weapon",
  face_covering_observed: "Face covering observed",
  camera_offline: "Camera offline",
  camera_obstructed: "Camera obstructed",
  camera_obstruction_cleared: "Obstruction cleared",
};

export const ROLE_LABEL: Record<string, string> = {
  org_admin: "Organisation admin",
  site_manager: "Site manager",
  security_reviewer: "Security reviewer",
  auditor: "Read-only auditor",
};

export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function fmtTime(iso: string | null | undefined, tz?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return new Intl.DateTimeFormat("en-AU", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: tz,
  }).format(d);
}

export function fmtRelative(iso: string | null | undefined): string {
  if (!iso) return "never";
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return `${Math.round(s / 86400)}d ago`;
}

export function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

export function fmtOffset(s: number | null | undefined): string {
  if (s === null || s === undefined) return "—";
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1).padStart(4, "0");
  return `${m}:${sec}`;
}

export function describeWindows(ws: { days: number[]; start: string; end: string }[]): string {
  if (!ws.length) return "Always";
  return ws
    .map((w) => {
      const days = w.days.length === 7 ? "Every day" : w.days.map((d) => DAYS[d]).join(", ");
      return `${days} ${w.start}–${w.end}${w.end <= w.start ? " (overnight)" : ""}`;
    })
    .join("; ");
}
