import { ShieldCheck } from "lucide-react";

export function AuthCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-2">
          <ShieldCheck className="h-7 w-7 text-teal" aria-hidden />
          <div>
            <div className="text-base font-semibold">ZoneGuard AI</div>
            <div className="text-xs text-ink-faint">Your Cameras. Smarter Security. Privacy by Design.</div>
          </div>
        </div>
        <div className="rounded-lg border border-line bg-surface p-6">
          <h1 className="text-lg font-semibold">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-ink-muted">{subtitle}</p> : null}
          <div className="mt-5">{children}</div>
        </div>
      </div>
    </div>
  );
}
