"use client";

import { Trash2, Undo2 } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import type { Point } from "@/lib/types";

export interface Shape {
  id: string;
  points: Point[];
  kind: "area" | "line" | "mask";
  label: string;
  highlight?: boolean;
}

const COLORS = { area: "#2DD4BF", line: "#F5C451", mask: "#94A3B8" };

/** Click on the camera still to add points. Coordinates are normalised (0..1) so they are
 *  independent of camera resolution. */
export function PolygonEditor({ imageUrl, shapes, draft, onDraftChange, mode, disabled }: {
  imageUrl: string | null;
  shapes: Shape[];
  draft: Point[];
  onDraftChange: (pts: Point[]) => void;
  mode: "area" | "line" | "mask";
  disabled?: boolean;
}) {
  const ref = React.useRef<HTMLDivElement>(null);
  const [imgError, setImgError] = React.useState(false);
  React.useEffect(() => setImgError(false), [imageUrl]);

  const add = (e: React.MouseEvent) => {
    if (disabled || !ref.current) return;
    if (mode === "line" && draft.length >= 2) return;
    const r = ref.current.getBoundingClientRect();
    const x = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    const y = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
    onDraftChange([...draft, [Number(x.toFixed(4)), Number(y.toFixed(4))]]);
  };

  const poly = (pts: Point[]) => pts.map((p) => `${p[0]},${p[1]}`).join(" ");

  return (
    <div>
      <div
        ref={ref}
        onClick={add}
        data-testid="zone-canvas"
        className="relative aspect-video w-full cursor-crosshair select-none overflow-hidden rounded-md border border-line bg-black"
      >
        {imageUrl && !imgError ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imageUrl} alt="Camera preview (privacy masks applied)" className="absolute inset-0 h-full w-full object-fill" draggable={false} onError={() => setImgError(true)} />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <p className="max-w-md text-center text-xs text-ink-faint">
              No preview yet. Upload a staged video for this camera, or run <code className="text-ink-muted">zoneguard-edge snapshot</code> on
              the edge agent. You can still draw on the blank canvas.
            </p>
          </div>
        )}
        <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
          {shapes.map((s) =>
            s.kind === "line" ? (
              <polyline key={s.id} points={poly(s.points)} fill="none" stroke={COLORS.line} strokeWidth={s.highlight ? 0.008 : 0.005} />
            ) : (
              <polygon key={s.id} points={poly(s.points)} fill={s.kind === "mask" ? "rgba(15,23,42,0.85)" : "rgba(45,212,191,0.18)"}
                stroke={COLORS[s.kind]} strokeWidth={s.highlight ? 0.006 : 0.003} />
            ),
          )}
          {draft.length > 0 ? (
            mode === "line" || draft.length < 3 ? (
              <polyline points={poly(draft)} fill="none" stroke="#fff" strokeDasharray="0.01 0.008" strokeWidth={0.004} />
            ) : (
              <polygon points={poly(draft)} fill="rgba(255,255,255,0.15)" stroke="#fff" strokeDasharray="0.01 0.008" strokeWidth={0.004} />
            )
          ) : null}
          {draft.map((pt, i) => (
            <circle key={i} cx={pt[0]} cy={pt[1]} r={0.008} fill="#fff" />
          ))}
        </svg>
        {shapes.map((s) => (
          <span key={`l-${s.id}`} className="pointer-events-none absolute rounded bg-black/70 px-1 text-[10px] text-ink"
            style={{ left: `${s.points[0][0] * 100}%`, top: `${s.points[0][1] * 100}%` }}>{s.label}</span>
        ))}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
        <span>
          {mode === "line" ? "Click two points to set the entrance boundary (A → B)." : "Click to add polygon points (min 3)."} Points: {draft.length}
        </span>
        <Button type="button" size="sm" variant="ghost" onClick={() => onDraftChange(draft.slice(0, -1))} disabled={!draft.length}><Undo2 /> Undo</Button>
        <Button type="button" size="sm" variant="ghost" onClick={() => onDraftChange([])} disabled={!draft.length}><Trash2 /> Clear</Button>
      </div>
    </div>
  );
}
