import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A1020",
        surface: { DEFAULT: "#0F172A", 2: "#141F36", 3: "#1A2742" },
        line: "#22304D",
        ink: { DEFAULT: "#E6ECF5", muted: "#9AA8C2", faint: "#6B7A97" },
        teal: { DEFAULT: "#2DD4BF", strong: "#14B8A6", dim: "#0F3D3A" },
        sev: {
          info: "#7DA6FF",
          review: "#F5C451",
          high: "#FB923C",
          critical: "#F87171",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: { lg: "10px", md: "8px", sm: "6px" },
    },
  },
  plugins: [],
} satisfies Config;
