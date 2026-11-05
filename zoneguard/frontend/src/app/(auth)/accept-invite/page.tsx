"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";
import { ErrorText } from "@/components/ui/misc";
import { api } from "@/lib/api";

import { AuthCard } from "../auth-card";

function AcceptForm() {
  const router = useRouter();
  const token = useSearchParams().get("token") || "";
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ org_id: string; mfa_required: boolean }>("/api/auth/invitations/accept", {
        body: { token, full_name: name || null, password },
      });
      router.replace(r.mfa_required ? "/login" : `/?org=${r.org_id}`);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard title="Accept invitation" subtitle="New to ZoneGuard? Set your name and a password. Existing users: enter your current password.">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Full name (new accounts)" htmlFor="name"><Input id="name" value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label="Password" htmlFor="password"><Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <ErrorText error={error} />
        <Button type="submit" className="w-full" disabled={busy || !token}>Accept and continue</Button>
      </form>
    </AuthCard>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={null}>
      <AcceptForm />
    </Suspense>
  );
}
