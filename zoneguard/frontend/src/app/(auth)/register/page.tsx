"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";
import { ErrorText } from "@/components/ui/misc";
import { api } from "@/lib/api";

import { AuthCard } from "../auth-card";

export default function RegisterPage() {
  const router = useRouter();
  const [f, setF] = useState({ organisation_name: "", full_name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api("/api/auth/register", { body: f });
      router.replace("/");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard title="Register your organisation" subtitle="You will become the organisation administrator.">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Organisation name" htmlFor="org"><Input id="org" required value={f.organisation_name} onChange={set("organisation_name")} /></Field>
        <Field label="Your full name" htmlFor="name"><Input id="name" required autoComplete="name" value={f.full_name} onChange={set("full_name")} /></Field>
        <Field label="Work email" htmlFor="email"><Input id="email" type="email" required autoComplete="email" value={f.email} onChange={set("email")} /></Field>
        <Field label="Password" htmlFor="password" hint="At least 12 characters with upper and lower case letters and a digit.">
          <Input id="password" type="password" required minLength={12} autoComplete="new-password" value={f.password} onChange={set("password")} />
        </Field>
        <ErrorText error={error} />
        <Button type="submit" className="w-full" disabled={busy}>{busy ? "Creating…" : "Create organisation"}</Button>
      </form>
      <p className="mt-5 text-center text-xs text-ink-muted">
        Already registered? <Link className="text-teal hover:underline" href="/login">Sign in</Link>
      </p>
    </AuthCard>
  );
}
