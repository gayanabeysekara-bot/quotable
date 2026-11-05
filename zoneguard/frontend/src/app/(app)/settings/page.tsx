"use client";

import { Copy, Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form";
import { Badge, Callout, ErrorText, Spinner, Table, Tabs, Td, Th, PageHeader } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { ROLE_LABEL, fmtRelative, fmtTime } from "@/lib/format";
import { useData, useOrg } from "@/lib/org-context";
import type { Member, Role } from "@/lib/types";

type Tab = "members" | "sites" | "edge" | "privacy" | "retention" | "audit" | "security";

function Members() {
  const { p, can, me } = useOrg();
  const members = useData<Member[]>(p("/members"));
  const invites = useData<{ id: string; email: string; role: string; expires_at: string; accepted_at: string | null; revoked_at: string | null }[]>(can("manage_members") ? p("/invitations") : null);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("security_reviewer");
  const [link, setLink] = useState("");
  const [error, setError] = useState<unknown>(null);
  const invite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const r = await api<{ invite_link: string }>(p("/invitations"), { body: { email, role } });
      setLink(r.invite_link);
      setEmail("");
      invites.reload();
    } catch (err) { setError(err); }
  };
  const changeRole = async (m: Member, r: string) => {
    try { await api(p(`/members/${m.user_id}`), { method: "PATCH", body: { role: r } }); } catch (err) { setError(err); }
    members.reload();
  };
  const remove = async (m: Member) => {
    if (!confirm(`Remove ${m.email} from this organisation?`)) return;
    try { await api(p(`/members/${m.user_id}`), { method: "DELETE" }); } catch (err) { setError(err); }
    members.reload();
  };
  return (
    <div className="space-y-5">
      <Card>
        <CardHeader><div><CardTitle>Members & permissions</CardTitle><CardDescription>Permissions are enforced by the server for every request.</CardDescription></div></CardHeader>
        <CardContent className="p-0">
          <Table>
            <thead><tr><Th>Member</Th><Th>Role</Th><Th>MFA</Th><Th /></tr></thead>
            <tbody>
              {(members.data ?? []).map((m) => (
                <tr key={m.user_id}>
                  <Td><div className="font-medium">{m.full_name}</div><div className="text-xs text-ink-faint">{m.email}</div></Td>
                  <Td>{can("manage_members") && m.user_id !== me.id ? (
                    <Select aria-label={`Role for ${m.email}`} className="w-52" value={m.role} onChange={(e) => changeRole(m, e.target.value)}>
                      {Object.entries(ROLE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </Select>) : ROLE_LABEL[m.role]}</Td>
                  <Td>{m.mfa_enabled ? <Badge tone="teal">enabled</Badge> : <Badge tone="muted">off</Badge>}</Td>
                  <Td className="text-right">{can("manage_members") && m.user_id !== me.id ? <Button size="icon" variant="ghost" aria-label={`Remove ${m.email}`} onClick={() => remove(m)}><Trash2 /></Button> : null}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </CardContent>
      </Card>
      {can("manage_members") ? (
        <Card>
          <CardHeader><div><CardTitle>Invite a member</CardTitle><CardDescription>Invitations expire after 7 days and can be used once.</CardDescription></div></CardHeader>
          <CardContent>
            <form onSubmit={invite} className="grid gap-3 sm:grid-cols-[1fr_220px_auto] sm:items-end">
              <Field label="Email" htmlFor="i-email"><Input id="i-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
              <Field label="Role" htmlFor="i-role"><Select id="i-role" value={role} onChange={(e) => setRole(e.target.value as Role)}>{Object.entries(ROLE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></Field>
              <Button type="submit">Send invitation</Button>
            </form>
            <ErrorText error={error} />
            {link ? (
              <div className="mt-3 flex items-center gap-2 rounded-md border border-line bg-surface-2 p-2 text-xs">
                <code className="flex-1 truncate">{link}</code>
                <Button size="sm" variant="ghost" onClick={() => navigator.clipboard.writeText(link)}><Copy /> Copy</Button>
              </div>
            ) : null}
            {invites.data?.filter((i) => !i.accepted_at && !i.revoked_at).length ? (
              <ul className="mt-4 space-y-1 text-xs text-ink-muted">
                {invites.data.filter((i) => !i.accepted_at && !i.revoked_at).map((i) => (
                  <li key={i.id} className="flex items-center justify-between">
                    <span>{i.email} · {ROLE_LABEL[i.role]} · expires {fmtTime(i.expires_at)}</span>
                    <Button size="sm" variant="ghost" onClick={async () => { await api(p(`/invitations/${i.id}`), { method: "DELETE" }); invites.reload(); }}>Revoke</Button>
                  </li>
                ))}
              </ul>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function Sites() {
  const { p, sites, refreshSites, can } = useOrg();
  const [f, setF] = useState({ name: "", address: "", timezone: "Australia/Sydney" });
  const [error, setError] = useState<unknown>(null);
  const zones = ["Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane", "Australia/Adelaide", "Australia/Darwin", "Australia/Perth", "Australia/Hobart", "Pacific/Auckland", "UTC"];
  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try { await api(p("/sites"), { body: f }); setF({ ...f, name: "", address: "" }); await refreshSites(); } catch (err) { setError(err); }
  };
  return (
    <Card>
      <CardHeader><div><CardTitle>Sites</CardTitle><CardDescription>Schedules are evaluated in each site’s timezone.</CardDescription></div></CardHeader>
      <CardContent>
        <ul className="mb-4 divide-y divide-line/60">
          {sites.map((s) => <li key={s.id} className="flex justify-between py-2 text-sm"><span>{s.name} <span className="text-xs text-ink-faint">{s.address}</span></span><span className="text-xs text-ink-faint">{s.timezone}</span></li>)}
          {!sites.length ? <li className="py-2 text-sm text-ink-muted">No sites yet.</li> : null}
        </ul>
        {can("manage_sites") ? (
          <form onSubmit={add} className="grid gap-3 sm:grid-cols-[1fr_1fr_200px_auto] sm:items-end">
            <Field label="Site name" htmlFor="s-name"><Input id="s-name" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
            <Field label="Address" htmlFor="s-addr"><Input id="s-addr" value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} /></Field>
            <Field label="Timezone" htmlFor="s-tz"><Select id="s-tz" value={f.timezone} onChange={(e) => setF({ ...f, timezone: e.target.value })}>{zones.map((z) => <option key={z}>{z}</option>)}</Select></Field>
            <Button type="submit">Create site</Button>
          </form>
        ) : null}
        <ErrorText error={error} />
      </CardContent>
    </Card>
  );
}

function Edge() {
  const { p, sites, can } = useOrg();
  const agents = useData<{ id: string; site_id: string; name: string; token_prefix: string; version: string; last_seen_at: string | null; stats: Record<string, unknown>; revoked_at: string | null }[]>(p("/edge-agents"), { poll: 15000 });
  const [f, setF] = useState({ site_id: "", name: "" });
  const [token, setToken] = useState("");
  const [error, setError] = useState<unknown>(null);
  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try { const r = await api<{ token: string }>(p("/edge-agents"), { body: f }); setToken(r.token); agents.reload(); } catch (err) { setError(err); }
  };
  return (
    <div className="space-y-5">
      <Callout title="How live cameras connect">The edge agent runs on a small computer inside your network, pulls RTSP streams read-only, runs detection locally and sends only event metadata (no video) to ZoneGuard over HTTPS. It buffers events during internet outages.</Callout>
      <Card>
        <CardHeader><CardTitle>Edge agents</CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <thead><tr><Th>Agent</Th><Th>Site</Th><Th>Last seen</Th><Th>Queue</Th><Th>ONVIF discovered</Th><Th /></tr></thead>
            <tbody>
              {(agents.data ?? []).map((a) => (
                <tr key={a.id}>
                  <Td><div className="font-medium">{a.name}</div><div className="font-mono text-[11px] text-ink-faint">{a.token_prefix}… {a.version ? `v${a.version}` : ""}</div></Td>
                  <Td className="text-xs">{sites.find((s) => s.id === a.site_id)?.name}</Td>
                  <Td className="text-xs">{a.revoked_at ? <Badge tone="critical">revoked</Badge> : fmtRelative(a.last_seen_at)}</Td>
                  <Td className="tabular text-xs">{String(a.stats?.queue_depth ?? "—")}</Td>
                  <Td className="text-xs">{Array.isArray(a.stats?.onvif_discovered) ? (a.stats.onvif_discovered as { xaddrs: string[] }[]).map((d, i) => <div key={i} className="font-mono text-[11px]">{d.xaddrs[0]}</div>) : "—"}</Td>
                  <Td className="text-right">{can("manage_edge") && !a.revoked_at ? <Button size="sm" variant="ghost" onClick={async () => { if (confirm("Revoke this agent? It will stop syncing immediately.")) { await api(p(`/edge-agents/${a.id}`), { method: "DELETE" }); agents.reload(); } }}>Revoke</Button> : null}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </CardContent>
      </Card>
      {can("manage_edge") ? (
        <Card>
          <CardHeader><CardTitle>Register an edge agent</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={create} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
              <Field label="Site" htmlFor="e-site"><Select id="e-site" required value={f.site_id} onChange={(e) => setF({ ...f, site_id: e.target.value })}><option value="" disabled>Select</option>{sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</Select></Field>
              <Field label="Agent name" htmlFor="e-name"><Input id="e-name" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
              <Button type="submit">Create token</Button>
            </form>
            <ErrorText error={error} />
            {token ? (
              <Callout tone="warn" title="Copy this token now — it is shown only once" className="mt-3">
                <code className="block break-all text-ink">{token}</code>
                <span className="mt-1 block">Set it as ZG_EDGE_TOKEN on the edge device (see README → Edge agent).</span>
              </Callout>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function Privacy() {
  const { p, org, refreshOrg, can } = useOrg();
  const [f, setF] = useState({ weapon_detection_mode: org.weapon_detection_mode, face_covering_mode: org.face_covering_mode, privacy_contact_email: org.privacy_contact_email });
  const [confirm, setConfirm] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState<unknown>(null);
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try { await api(p(""), { method: "PATCH", body: { ...f, ...(confirm ? { confirm_surveillance_notice: true } : {}) } }); await refreshOrg(); setMsg("Saved."); } catch (err) { setError(err); }
  };
  const ro = !can("manage_org");
  return (
    <Card>
      <CardHeader><div><CardTitle>Privacy & optional detection modules</CardTitle><CardDescription>Specialist modules are off by default and opt-in per organisation.</CardDescription></div></CardHeader>
      <CardContent>
        <form onSubmit={save} className="space-y-4">
          <div className="rounded-md border border-line bg-surface-2 p-3 text-xs text-ink-muted">
            <div className="mb-1 font-semibold text-ink">Fixed privacy safeguards (cannot be turned off)</div>
            <ul className="list-disc space-y-0.5 pl-4">
              <li>No facial recognition, face templates or identity matching; no demographic inference.</li>
              <li>Anonymous track IDs only, local to one camera; no cross-camera tracking.</li>
              <li>Video and images are never sent to external AI services.</li>
              <li>Alert emails contain no images.</li>
              <li>No automatic contact with police/emergency services; no automatic physical actions.</li>
            </ul>
          </div>
          <Field label="Visible-weapon module (experimental)" htmlFor="p-weapon" hint="No validated weapon model is bundled. Outputs are labelled as possible objects and require human review.">
            <Select id="p-weapon" disabled={ro} value={f.weapon_detection_mode} onChange={(e) => setF({ ...f, weapon_detection_mode: e.target.value })}>
              <option value="disabled">Disabled</option>
              <option value="simulated_test">Simulated test mode (labelled, for workflow testing)</option>
              <option value="coco_knife_unvalidated">Experimental: generic COCO “knife” class (unvalidated, no firearms)</option>
            </Select>
          </Field>
          <Field label="Face-covering observations (optional)" htmlFor="p-face" hint="Neutral observation only, capped at Informational. No model is bundled; simulated mode is for testing.">
            <Select id="p-face" disabled={ro} value={f.face_covering_mode} onChange={(e) => setF({ ...f, face_covering_mode: e.target.value })}>
              <option value="disabled">Disabled</option>
              <option value="simulated_test">Simulated test mode (labelled)</option>
            </Select>
          </Field>
          <Field label="Privacy contact email" htmlFor="p-contact"><Input id="p-contact" type="email" disabled={ro} value={f.privacy_contact_email} onChange={(e) => setF({ ...f, privacy_contact_email: e.target.value })} /></Field>
          <div className="rounded-md border border-line p-3 text-sm">
            <div className="mb-1">Surveillance notice: {org.surveillance_notice_confirmed_at ? <Badge tone="teal">confirmed {fmtTime(org.surveillance_notice_confirmed_at)}</Badge> : <Badge tone="review">not confirmed</Badge>}</div>
            <Checkbox disabled={ro} checked={confirm} onChange={(e) => setConfirm(e.target.checked)}
              label={<span className="text-xs text-ink-muted">I confirm required surveillance notices (e.g. workplace surveillance notice periods, visible signage, school community notification) are in place for monitored sites, and legal advice has been obtained where needed. This is recorded in the audit log.</span>} />
          </div>
          <ErrorText error={error} />
          {msg ? <p className="text-xs text-teal" role="status">{msg}</p> : null}
          {!ro ? <Button type="submit">Save privacy settings</Button> : null}
        </form>
      </CardContent>
    </Card>
  );
}

function Retention() {
  const { p, org, refreshOrg, can } = useOrg();
  const [f, setF] = useState({ video_retention_days: org.video_retention_days, detection_retention_days: org.detection_retention_days, event_retention_days: org.event_retention_days, incident_retention_days: org.incident_retention_days, audit_retention_days: org.audit_retention_days });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState<unknown>(null);
  const ro = !can("manage_org");
  const fields: [keyof typeof f, string, string][] = [
    ["video_retention_days", "Uploaded raw video (1–90 days)", "Deleted from disk automatically."],
    ["detection_retention_days", "Per-frame detections (1–365)", "Bounding-box metadata for review."],
    ["event_retention_days", "Detection events (1–1095)", "Events linked to an incident are kept with it."],
    ["incident_retention_days", "Closed/dismissed incidents (30–2555)", "Includes their history."],
    ["audit_retention_days", "Audit log (365–3650)", ""],
  ];
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try { await api(p(""), { method: "PATCH", body: f }); await refreshOrg(); setMsg("Saved."); } catch (err) { setError(err); }
  };
  return (
    <Card>
      <CardHeader><div><CardTitle>Retention & deletion</CardTitle><CardDescription>A sweep runs hourly. Confirm periods against your records obligations (e.g. state records acts for schools).</CardDescription></div></CardHeader>
      <CardContent>
        <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
          {fields.map(([k, label, hint]) => (
            <Field key={k} label={label} htmlFor={k} hint={hint}><Input id={k} type="number" disabled={ro} value={f[k]} onChange={(e) => setF({ ...f, [k]: Number(e.target.value) })} /></Field>
          ))}
          <div className="flex items-end gap-2 sm:col-span-2">
            {!ro ? <Button type="submit">Save retention</Button> : null}
            {!ro ? <Button type="button" variant="outline" onClick={async () => { const r = await api<Record<string, number>>(p("/retention/run"), { method: "POST" }); setMsg(`Sweep complete: ${Object.entries(r).map(([k, v]) => `${v} ${k}`).join(", ")}`); }}>Run sweep now</Button> : null}
          </div>
          <div className="sm:col-span-2"><ErrorText error={error} />{msg ? <p className="text-xs text-teal" role="status">{msg}</p> : null}</div>
        </form>
      </CardContent>
    </Card>
  );
}

function Audit() {
  const { p, can, org } = useOrg();
  const { data, error } = useData<{ id: string; actor_type: string; actor_label: string; action: string; target_type: string; target_id: string; ip: string; created_at: string; details: Record<string, unknown> }[]>(can("view_audit") ? p("/audit?limit=300") : null);
  if (!can("view_audit")) return <Callout>Your role cannot view the audit log.</Callout>;
  return (
    <Card>
      <CardHeader><div><CardTitle>Audit log</CardTitle><CardDescription>Security-relevant actions. Secrets are redacted.</CardDescription></div></CardHeader>
      <CardContent className="p-0">
        <ErrorText error={error} />
        {!data ? <div className="p-5"><Spinner /></div> : (
          <Table>
            <thead><tr><Th>Time</Th><Th>Actor</Th><Th>Action</Th><Th>Target</Th><Th>Details</Th></tr></thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.id}>
                  <Td className="whitespace-nowrap text-xs text-ink-muted">{fmtTime(a.created_at, org.timezone)}</Td>
                  <Td className="text-xs">{a.actor_label || a.actor_type}<div className="text-[11px] text-ink-faint">{a.ip}</div></Td>
                  <Td className="font-mono text-xs">{a.action}</Td>
                  <Td className="text-xs text-ink-muted">{a.target_type}</Td>
                  <Td className="max-w-xs truncate font-mono text-[11px] text-ink-faint" >{JSON.stringify(a.details)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function Security() {
  const { me } = useOrg();
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState<unknown>(null);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setError(null);
    try { await fn(); setMsg(ok); } catch (err) { setError(err); }
  };
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader><div><CardTitle>Two-factor authentication</CardTitle><CardDescription>TOTP (authenticator app). Strongly recommended for admins.</CardDescription></div></CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">Status: {me.mfa_enabled ? <Badge tone="teal">enabled</Badge> : <Badge tone="review">not enabled</Badge>}</p>
          {!me.mfa_enabled && !setup ? <Button onClick={() => run(async () => setSetup(await api("/api/auth/mfa/setup", { method: "POST" })), "")}>Set up MFA</Button> : null}
          {setup ? (
            <div className="space-y-2 text-xs">
              <p className="text-ink-muted">Add this secret to your authenticator app, then enter the 6-digit code.</p>
              <code className="block break-all rounded bg-surface-2 p-2">{setup.secret}</code>
              <code className="block break-all text-[10px] text-ink-faint">{setup.otpauth_uri}</code>
            </div>
          ) : null}
          {setup || me.mfa_enabled ? (
            <div className="flex items-end gap-2">
              <Field label="Code" htmlFor="mfa-code"><Input id="mfa-code" inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} /></Field>
              {me.mfa_enabled
                ? <Button variant="danger" onClick={() => run(() => api("/api/auth/mfa/disable", { body: { code } }), "MFA disabled. Reload to refresh.")}>Disable</Button>
                : <Button onClick={() => run(() => api("/api/auth/mfa/enable", { body: { code } }), "MFA enabled. Reload to refresh.")}>Enable</Button>}
            </div>
          ) : null}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><div><CardTitle>Change password</CardTitle><CardDescription>Signs out your other sessions.</CardDescription></div></CardHeader>
        <CardContent className="space-y-3">
          <Field label="Current password" htmlFor="pw-cur"><Input id="pw-cur" type="password" autoComplete="current-password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
          <Field label="New password" htmlFor="pw-new"><Input id="pw-new" type="password" autoComplete="new-password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
          <Button onClick={() => run(() => api("/api/auth/password", { body: pw }), "Password changed.")}>Update password</Button>
        </CardContent>
      </Card>
      <div className="lg:col-span-2"><ErrorText error={error} />{msg ? <p className="text-xs text-teal" role="status">{msg}</p> : null}</div>
    </div>
  );
}

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("members");
  const tabs: { id: Tab; label: string }[] = [
    { id: "members", label: "Members" }, { id: "sites", label: "Sites" }, { id: "edge", label: "Edge agents" },
    { id: "privacy", label: "Privacy" }, { id: "retention", label: "Retention" }, { id: "audit", label: "Audit log" }, { id: "security", label: "Account security" },
  ];
  return (
    <>
      <PageHeader title="Organisation Settings" />
      <Tabs tabs={tabs} value={tab} onChange={setTab} />
      <div className="mt-5">
        {tab === "members" ? <Members /> : tab === "sites" ? <Sites /> : tab === "edge" ? <Edge /> : tab === "privacy" ? <Privacy /> : tab === "retention" ? <Retention /> : tab === "audit" ? <Audit /> : <Security />}
      </div>
    </>
  );
}
