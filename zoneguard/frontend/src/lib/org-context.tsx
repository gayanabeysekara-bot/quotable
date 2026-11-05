"use client";

import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";

import { api, orgPath } from "./api";
import type { Me, Org, Site } from "./types";

interface OrgState {
  me: Me;
  org: Org;
  orgId: string;
  role: string;
  permissions: Set<string>;
  sites: Site[];
  siteId: string; // "" = all sites
  setSiteId: (id: string) => void;
  switchOrg: (id: string) => void;
  refreshOrg: () => Promise<void>;
  refreshSites: () => Promise<void>;
  can: (perm: string) => boolean;
  p: (path?: string) => string;
}

const Ctx = React.createContext<OrgState | null>(null);

function store(key: string, value?: string): string | null {
  try {
    if (value !== undefined) localStorage.setItem(key, value);
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const search = useSearchParams();
  const [me, setMe] = React.useState<Me | null>(null);
  const [orgId, setOrgId] = React.useState<string | null>(null);
  const [org, setOrg] = React.useState<Org | null>(null);
  const [role, setRole] = React.useState("");
  const [perms, setPerms] = React.useState<Set<string>>(new Set());
  const [sites, setSites] = React.useState<Site[]>([]);
  const [siteId, setSiteIdState] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    api<Me>("/api/auth/me")
      .then((m) => {
        setMe(m);
        if (!m.memberships.length) {
          setError("Your account is not a member of any organisation yet. Ask an administrator for an invitation.");
          return;
        }
        const wanted = search.get("org") || store("zg.org");
        const pick = m.memberships.find((x) => x.org_id === wanted) ?? m.memberships[0];
        setOrgId(pick.org_id);
      })
      .catch(() => router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshOrg = React.useCallback(async () => {
    if (!orgId) return;
    const [o, r] = await Promise.all([
      api<Org>(orgPath(orgId)),
      api<{ role: string; permissions: string[] }>(orgPath(orgId, "/me")),
    ]);
    setOrg(o);
    setRole(r.role);
    setPerms(new Set(r.permissions));
  }, [orgId]);

  const refreshSites = React.useCallback(async () => {
    if (!orgId) return;
    setSites(await api<Site[]>(orgPath(orgId, "/sites")));
  }, [orgId]);

  React.useEffect(() => {
    if (!orgId) return;
    store("zg.org", orgId);
    setSiteIdState(store(`zg.site.${orgId}`) || "");
    refreshOrg().catch((e) => setError(String(e.message || e)));
    refreshSites().catch(() => undefined);
  }, [orgId, refreshOrg, refreshSites]);

  if (error) {
    return <div className="mx-auto mt-24 max-w-md rounded-lg border border-line bg-surface p-6 text-sm text-ink-muted">{error}</div>;
  }
  if (!me || !org || !orgId) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-ink-muted">Loading ZoneGuard…</div>;
  }
  const value: OrgState = {
    me,
    org,
    orgId,
    role,
    permissions: perms,
    sites,
    siteId: sites.some((s) => s.id === siteId) ? siteId : "",
    setSiteId: (id) => {
      setSiteIdState(id);
      store(`zg.site.${orgId}`, id);
    },
    switchOrg: (id) => setOrgId(id),
    refreshOrg,
    refreshSites,
    can: (p) => perms.has(p),
    p: (path = "") => orgPath(orgId, path),
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useOrg(): OrgState {
  const v = React.useContext(Ctx);
  if (!v) throw new Error("useOrg must be used inside OrgProvider");
  return v;
}

/** Small data-fetching hook with manual reload and optional polling. */
export function useData<T>(path: string | null, opts: { poll?: number } = {}) {
  const [data, setData] = React.useState<T | null>(null);
  const [error, setError] = React.useState<unknown>(null);
  const [loading, setLoading] = React.useState(false);
  const reload = React.useCallback(async () => {
    if (!path) return;
    setLoading(true);
    try {
      setData(await api<T>(path));
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [path]);
  React.useEffect(() => {
    reload();
    if (!opts.poll || !path) return;
    const t = setInterval(reload, opts.poll);
    return () => clearInterval(t);
  }, [reload, opts.poll, path]);
  return { data, error, loading, reload, setData };
}
