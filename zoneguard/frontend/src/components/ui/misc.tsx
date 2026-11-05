"use client";

import { AlertTriangle, Info, Loader2, X } from "lucide-react";
import * as React from "react";

import { SEVERITY_LABEL } from "@/lib/format";
import type { Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

export function Badge({ className, tone = "neutral", ...p }: React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "teal" | "info" | "review" | "high" | "critical" | "muted";
}) {
  const tones = {
    neutral: "bg-surface-3 text-ink border-line",
    teal: "bg-teal-dim text-teal border-[#155e57]",
    info: "bg-[#14213F] text-sev-info border-[#243A6B]",
    review: "bg-[#33290F] text-sev-review border-[#5A4716]",
    high: "bg-[#3A230F] text-sev-high border-[#62391A]",
    critical: "bg-[#3A1418] text-sev-critical border-[#5B1D24]",
    muted: "bg-transparent text-ink-faint border-line",
  } as const;
  return (
    <span
      className={cn("inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium", tones[tone], className)}
      {...p}
    />
  );
}

const SEV_TONE: Record<Severity, "info" | "review" | "high" | "critical"> = {
  informational: "info",
  review_required: "review",
  high_priority: "high",
  critical_review: "critical",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge tone={SEV_TONE[severity]}>{SEVERITY_LABEL[severity]}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "online" || status === "completed" || status === "closed"
      ? "teal"
      : status === "offline" || status === "failed" || status === "open"
        ? "critical"
        : status === "degraded" || status === "running" || status === "escalated"
          ? "high"
          : status === "acknowledged" || status === "queued"
            ? "review"
            : "muted";
  return <Badge tone={tone}>{status.replace("_", " ")}</Badge>;
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-4 w-4 animate-spin text-ink-muted", className)} aria-label="Loading" />;
}

export function Callout({ tone = "info", title, children, className }: {
  tone?: "info" | "warn" | "danger";
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const styles = {
    info: "border-[#243A6B] bg-[#0F1A33] text-ink",
    warn: "border-[#5A4716] bg-[#211B0B] text-ink",
    danger: "border-[#5B1D24] bg-[#22100F] text-ink",
  };
  const Icon = tone === "info" ? Info : AlertTriangle;
  return (
    <div role={tone === "danger" ? "alert" : "note"} className={cn("flex gap-3 rounded-md border px-3 py-2.5 text-xs", styles[tone], className)}>
      <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", tone === "info" ? "text-sev-info" : tone === "warn" ? "text-sev-review" : "text-sev-critical")} />
      <div>
        {title ? <div className="mb-0.5 font-semibold">{title}</div> : null}
        <div className="text-ink-muted">{children}</div>
      </div>
    </div>
  );
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <p role="alert" className="text-xs text-sev-critical">
      {msg}
    </p>
  );
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-line px-6 py-10 text-center">
      <p className="text-sm font-medium text-ink">{title}</p>
      {children ? <div className="mt-1 text-xs text-ink-muted">{children}</div> : null}
    </div>
  );
}

export function Dialog({ open, onClose, title, children, wide }: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  React.useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-[8vh]" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn("w-full rounded-lg border border-line bg-surface shadow-2xl", wide ? "max-w-3xl" : "max-w-lg")}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-3">
          <h2 className="text-sm font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="rounded p-1 text-ink-muted hover:bg-surface-2 hover:text-ink">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  return (
    <div role="tablist" className="flex gap-1 overflow-x-auto border-b border-line">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm",
            value === t.id ? "border-teal text-ink" : "border-transparent text-ink-muted hover:text-ink",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full min-w-[640px] text-left text-sm">{children}</table>
    </div>
  );
}
export function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={cn("border-b border-line px-3 py-2 text-[11px] font-medium uppercase tracking-wider text-ink-faint", className)}>{children}</th>;
}
export function Td({ children, className, colSpan }: { children?: React.ReactNode; className?: string; colSpan?: number }) {
  return <td colSpan={colSpan} className={cn("border-b border-line/60 px-3 py-2.5 align-middle", className)}>{children}</td>;
}

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-ink">{title}</h1>
        {description ? <p className="mt-1 max-w-2xl text-sm text-ink-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function Stat({ label, value, sub, tone }: { label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: "critical" | "teal" }) {
  return (
    <div className="rounded-lg border border-line bg-surface px-4 py-3">
      <div className="text-[11px] font-medium uppercase tracking-wider text-ink-faint">{label}</div>
      <div className={cn("mt-1 text-2xl font-semibold tabular", tone === "critical" ? "text-sev-critical" : tone === "teal" ? "text-teal" : "text-ink")}>{value}</div>
      {sub ? <div className="mt-0.5 text-xs text-ink-muted">{sub}</div> : null}
    </div>
  );
}
