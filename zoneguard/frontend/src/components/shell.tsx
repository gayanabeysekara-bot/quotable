"use client";

import {
  Activity,
  Bell,
  Camera,
  FileVideo,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  Shapes,
  ShieldCheck,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";

import { api } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/format";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/incidents", label: "Incident Centre", icon: Bell },
  { href: "/cameras", label: "Cameras", icon: Camera },
  { href: "/analysis", label: "Video Analysis", icon: FileVideo },
  { href: "/zones", label: "Zones", icon: Shapes },
  { href: "/rules", label: "Rules & Alerts", icon: Activity },
  { href: "/evaluation", label: "Evaluation", icon: Gauge },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { me, org, orgId, role, sites, siteId, setSiteId, switchOrg } = useOrg();
  const path = usePathname();
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => setOpen(false), [path]);

  const logout = async () => {
    await api("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    window.location.href = "/login";
  };

  const sidebar = (
    <nav aria-label="Main" className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-5 py-5">
        <ShieldCheck className="h-6 w-6 text-teal" aria-hidden />
        <div>
          <div className="text-sm font-semibold tracking-wide">ZoneGuard AI</div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-ink-faint">Privacy by design</div>
        </div>
      </div>
      <ul className="flex-1 space-y-0.5 px-3">
        {NAV.map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          return (
            <li key={n.href}>
              <Link
                href={n.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm",
                  active ? "bg-surface-3 text-ink" : "text-ink-muted hover:bg-surface-2 hover:text-ink",
                )}
              >
                <n.icon className={cn("h-4 w-4", active && "text-teal")} aria-hidden />
                {n.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="border-t border-line p-4 text-xs">
        <div className="truncate text-ink">{me.full_name || me.email}</div>
        <div className="truncate text-ink-faint">{ROLE_LABEL[role] ?? role}</div>
        <button onClick={logout} className="mt-3 flex items-center gap-2 text-ink-muted hover:text-ink">
          <LogOut className="h-3.5 w-3.5" /> Sign out
        </button>
      </div>
    </nav>
  );

  return (
    <div className="min-h-screen lg:pl-60">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-line bg-surface lg:block">{sidebar}</aside>
      {open ? (
        <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)}>
          <aside className="h-full w-64 border-r border-line bg-surface" onClick={(e) => e.stopPropagation()}>
            {sidebar}
          </aside>
        </div>
      ) : null}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-bg/95 px-4 backdrop-blur sm:px-6">
        <button className="rounded p-1.5 text-ink-muted hover:bg-surface-2 lg:hidden" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen(!open)}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <label className="sr-only" htmlFor="org-select">Organisation</label>
        <select
          id="org-select"
          value={orgId}
          onChange={(e) => switchOrg(e.target.value)}
          className="h-8 max-w-[11rem] truncate rounded-md border border-line bg-surface-2 px-2 text-sm"
        >
          {me.memberships.map((m) => (
            <option key={m.org_id} value={m.org_id}>{m.org_name}</option>
          ))}
        </select>
        <label className="sr-only" htmlFor="site-select">Site</label>
        <select
          id="site-select"
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
          className="h-8 max-w-[11rem] truncate rounded-md border border-line bg-surface-2 px-2 text-sm"
        >
          <option value="">All sites</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <div className="ml-auto hidden text-xs text-ink-faint sm:block">{org.plan === "pilot" ? "Pilot programme" : org.plan}</div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}
