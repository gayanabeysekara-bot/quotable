"use client";

import { Suspense } from "react";

import { Shell } from "@/components/shell";
import { OrgProvider } from "@/lib/org-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <OrgProvider>
        <Shell>{children}</Shell>
      </OrgProvider>
    </Suspense>
  );
}
