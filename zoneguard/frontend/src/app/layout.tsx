import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "ZoneGuard AI",
  description: "Your Cameras. Smarter Security. Privacy by Design.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-AU">
      <body className="min-h-screen bg-bg font-sans text-ink">{children}</body>
    </html>
  );
}
