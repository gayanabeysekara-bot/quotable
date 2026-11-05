import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const PASSWORD = "Correct-Horse-42!";
const SAMPLE = process.env.ZG_SAMPLE_VIDEO || path.resolve(__dirname, "../../../samples/vtest.avi");
const MAIL_DIR = process.env.ZG_E2E_MAIL_DIR;

async function register(page: Page, email: string, org: string) {
  await page.goto("/register");
  await page.getByLabel("Organisation name").fill(org);
  await page.getByLabel("Your full name").fill("Pilot Admin");
  await page.getByLabel("Work email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create organisation" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
}

test("acceptance workflow through the dashboard", async ({ page, browser }) => {
  test.skip(!fs.existsSync(SAMPLE), "sample video not downloaded");
  const stamp = Date.now();
  const email = `admin-${stamp}@pilot.example.com`;
  const mailBefore = MAIL_DIR && fs.existsSync(MAIL_DIR) ? fs.readdirSync(MAIL_DIR).length : 0;

  // 1. log in (register, sign out, sign in again)
  await register(page, email, `Pilot School ${stamp}`);
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();

  // 2. create a site
  await page.getByRole("link", { name: "Settings" }).click();
  await page.getByRole("tab", { name: "Sites" }).click();
  await page.getByLabel("Site name").fill("Main Campus");
  await page.getByRole("button", { name: "Create site" }).click();
  await expect(page.getByRole("listitem").filter({ hasText: "Main Campus" })).toBeVisible();

  // camera for staged uploads
  await page.getByRole("link", { name: "Cameras" }).click();
  await page.getByRole("button", { name: "Add camera" }).click();
  await page.getByLabel("Camera name").fill("Admin corridor");
  await page.getByRole("button", { name: "Save camera" }).click();
  await expect(page.getByRole("cell", { name: "Admin corridor", exact: true })).toBeVisible();

  // 3. upload staged video (recorded 10 PM local = after hours)
  await page.getByRole("link", { name: "Video Analysis" }).click();
  await page.getByLabel("Camera").selectOption({ label: "Admin corridor" });
  await page.getByLabel("Recorded at (local time)").fill("2026-11-03T22:00");
  await page.getByLabel("Video file").setInputFiles(SAMPLE);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Upload" }).click();
  await expect(page.getByRole("button", { name: "vtest.avi", exact: true })).toBeVisible({ timeout: 60_000 });

  // 5. define a restricted zone (lower half) with the quick after-hours rule
  await page.getByRole("link", { name: "Zones" }).click();
  const canvas = page.getByTestId("zone-canvas");
  await expect(canvas.locator("img")).toBeVisible();
  const box = (await canvas.boundingBox())!;
  for (const [x, y] of [[0.02, 0.55], [0.98, 0.55], [0.98, 0.98], [0.02, 0.98]]) {
    await page.mouse.click(box.x + box.width * x, box.y + box.height * y);
  }
  await page.getByLabel("Zone name").fill("Finance Office");
  await page.getByRole("button", { name: "Save zone" }).click();
  await expect(page.getByText("Zone and after-hours rule created.")).toBeVisible();

  // 4 & 6. genuine person detection on the uploaded footage
  await page.getByRole("link", { name: "Video Analysis" }).click();
  await page.getByRole("button", { name: "vtest.avi", exact: true }).click();
  await page.getByLabel("Person model").selectOption("yolox_nano");
  await page.getByLabel("Frames / second").selectOption("2");
  await page.getByRole("button", { name: "Start analysis" }).click();
  await expect(page.getByText(/Avg inference/)).toBeVisible({ timeout: 150_000 });
  await expect(page.getByText("Model yolox_nano@0.1.1rc0")).toBeVisible();
  await expect(page.getByRole("button", { name: /Restricted-zone entry/ }).first()).toBeVisible();

  // 7 & 8. incident created by the after-hours rule appears in the Incident Centre
  await page.getByRole("link", { name: "Incident Centre" }).click();
  const row = page.getByRole("link", { name: /Person detected entering Finance Office/ }).first();
  await expect(row).toBeVisible();
  await row.click();
  await expect(page.getByText("Finance Office — after hours", { exact: true })).toBeVisible();

  // 9. email notification delivered via the configured SMTP test provider
  if (MAIL_DIR) {
    await expect.poll(() => (fs.existsSync(MAIL_DIR) ? fs.readdirSync(MAIL_DIR).length : 0)).toBeGreaterThan(mailBefore);
    const files = fs.readdirSync(MAIL_DIR).sort();
    const latest = fs.readFileSync(path.join(MAIL_DIR, files[files.length - 1]), "utf8");
    expect(latest).toContain(email);
    expect(latest).toContain("No images are attached");
  }

  // 10. reviewer actions
  await page.getByRole("button", { name: "Acknowledge" }).click();
  await expect(page.getByText("acknowledged", { exact: true }).first()).toBeVisible();
  await page.getByLabel("Note").fill("Checked the staff roster; escalating to site manager.");
  await page.getByRole("button", { name: "Escalate" }).click();
  await expect(page.getByText("escalated", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByRole("button", { name: "Confirm close" }).click();
  await expect(page.getByText("closed", { exact: true }).first()).toBeVisible();

  // 11. complete history
  const history = page.getByTestId("incident-history");
  for (const a of ["created", "acknowledge", "escalate", "close"]) {
    await expect(history.getByText(a, { exact: true })).toBeVisible();
  }
  const incidentUrl = page.url();
  const orgId = await page.locator("#org-select").inputValue();

  // 12. an unauthorised user cannot access this organisation's information
  const ctx = await browser.newContext();
  const other = await ctx.newPage();
  await register(other, `intruder-${stamp}@other.example.com`, `Other Org ${stamp}`);
  const apiRes = await other.request.get(`/api/orgs/${orgId}/incidents`);
  expect(apiRes.status()).toBe(404);
  await other.goto(`${incidentUrl}?org=${orgId}`);
  await expect(other.getByText("Incident not found")).toBeVisible();
  await expect(other.getByText("Finance Office")).toHaveCount(0);
  await ctx.close();
});
