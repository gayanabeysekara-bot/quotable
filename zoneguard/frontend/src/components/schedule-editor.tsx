"use client";

import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DAYS } from "@/lib/format";
import type { Window } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ScheduleEditor({ value, onChange, emptyLabel = "Always (no time restriction)", idPrefix }: {
  value: Window[];
  onChange: (w: Window[]) => void;
  emptyLabel?: string;
  idPrefix: string;
}) {
  const update = (i: number, patch: Partial<Window>) => onChange(value.map((w, j) => (j === i ? { ...w, ...patch } : w)));
  return (
    <div className="space-y-2">
      {value.length === 0 ? <p className="text-xs text-ink-faint">{emptyLabel}</p> : null}
      {value.map((w, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2 rounded-md border border-line bg-surface-2 p-2">
          <div className="flex gap-1" role="group" aria-label="Days">
            {DAYS.map((d, di) => {
              const on = w.days.includes(di);
              return (
                <button key={d} type="button" aria-pressed={on}
                  onClick={() => update(i, { days: on ? w.days.filter((x) => x !== di) : [...w.days, di].sort() })}
                  className={cn("h-7 w-9 rounded text-[11px]", on ? "bg-teal-dim text-teal" : "bg-surface-3 text-ink-faint")}>{d}</button>
              );
            })}
          </div>
          <label className="sr-only" htmlFor={`${idPrefix}-s-${i}`}>Start</label>
          <input id={`${idPrefix}-s-${i}`} type="time" value={w.start} onChange={(e) => update(i, { start: e.target.value })}
            className="h-8 rounded border border-line bg-surface px-2 text-sm" />
          <span className="text-xs text-ink-faint">to</span>
          <label className="sr-only" htmlFor={`${idPrefix}-e-${i}`}>End</label>
          <input id={`${idPrefix}-e-${i}`} type="time" value={w.end} onChange={(e) => update(i, { end: e.target.value })}
            className="h-8 rounded border border-line bg-surface px-2 text-sm" />
          {w.end <= w.start ? <span className="text-[11px] text-ink-faint">overnight</span> : null}
          <button type="button" aria-label="Remove window" onClick={() => onChange(value.filter((_, j) => j !== i))} className="ml-auto rounded p-1 text-ink-faint hover:text-ink">
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
      <Button type="button" size="sm" variant="outline" onClick={() => onChange([...value, { days: [0, 1, 2, 3, 4], start: "18:00", end: "06:00" }])}>
        <Plus /> Add time window
      </Button>
    </div>
  );
}
