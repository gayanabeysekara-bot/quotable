import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests run against an already-running stack (see README → Testing):
 *   API on :8000 (with model files), dashboard on :3000, SMTP sink writing to ZG_E2E_MAIL_DIR.
 */
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 180_000,
  expect: { timeout: 15_000 },
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.ZG_E2E_BASE_URL || "http://localhost:3000",
    timezoneId: "Australia/Sydney",
    locale: "en-AU",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
});
