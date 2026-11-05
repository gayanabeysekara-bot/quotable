"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";
import { ErrorText } from "@/components/ui/misc";
import { api } from "@/lib/api";

import { AuthCard } from "../auth-card";

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [mfa, setMfa] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const next = search.get("next");
  const dest = next && next.startsWith("/") && !next.startsWith("//") ? next : "/";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (!mfa) {
        const r = await api<{ mfa_required: boolean }>("/api/auth/login", { body: { email, password } });
        if (r.mfa_required) {
          setMfa(true);
          return;
        }
      } else {
        await api("/api/auth/mfa/verify", { body: { code } });
      }
      router.replace(dest);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard title={mfa ? "Two-factor verification" : "Sign in"} subtitle={mfa ? "Enter the 6-digit code from your authenticator app." : undefined}>
      <form onSubmit={submit} className="space-y-4">
        {!mfa ? (
          <>
            <Field label="Email" htmlFor="email">
              <Input id="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <Field label="Password" htmlFor="password">
              <Input id="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
          </>
        ) : (
          <Field label="Verification code" htmlFor="code">
            <Input id="code" inputMode="numeric" autoComplete="one-time-code" required maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
          </Field>
        )}
        <ErrorText error={error} />
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Signing in…" : mfa ? "Verify" : "Sign in"}
        </Button>
      </form>
      <p className="mt-5 text-center text-xs text-ink-muted">
        New organisation? <Link className="text-teal hover:underline" href="/register">Register</Link>
      </p>
    </AuthCard>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
