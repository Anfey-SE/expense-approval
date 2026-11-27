import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import * as fs from "fs";
import * as path from "path";

const BASE_URL = "http://localhost:5173";
const API_BASE = "http://localhost:8081";

const targetDirName = process.env.A11Y_PHASE || "before";
const outputDir = path.resolve(__dirname, "../../../evidence/m3/axe", targetDirName);

test.beforeAll(() => {
  fs.mkdirSync(outputDir, { recursive: true });
});

async function prepareRequestDetail(request: any): Promise<number> {
  const loginAlice = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email: "alice@acme.com", password: "password123" },
  });
  const aliceToken = (await loginAlice.json()).token;

  const createRes = await request.post(`${API_BASE}/api/requests`, {
    headers: { Authorization: `Bearer ${aliceToken}` },
    data: {
      title: `A11y Scan Expense ${Date.now()}`,
      description: "Axe scan expense item",
      currency: "USD",
      items: [
        {
          description: "Flight to conference",
          category: "Travel",
          amount: 220.5,
          incurredOn: new Date().toISOString().slice(0, 10),
        },
      ],
    },
  });
  const reqId = (await createRes.json()).id;

  await request.post(`${API_BASE}/api/requests/${reqId}/submit`, {
    headers: { Authorization: `Bearer ${aliceToken}` },
  });

  const loginBob = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email: "bob@acme.com", password: "password123" },
  });
  const bobToken = (await loginBob.json()).token;

  await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
    headers: { Authorization: `Bearer ${bobToken}` },
    data: { comment: "Bob endorsed" },
  });

  return reqId;
}

test.describe("Axe-core Accessibility Scans", () => {
  test("Scan Screen 1: Login Page (/login)", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page }).analyze();
    fs.writeFileSync(path.join(outputDir, "login.json"), JSON.stringify(results, null, 2));

    const crit = results.violations.filter((v) => v.impact === "critical").length;
    const ser = results.violations.filter((v) => v.impact === "serious").length;
    console.log(`[AXE] login: ${results.violations.length} violations (${crit} critical, ${ser} serious)`);
  });

  test("Scan Screen 2: Requests List (/)", async ({ page }) => {
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("alice@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page }).analyze();
    fs.writeFileSync(path.join(outputDir, "requests_list.json"), JSON.stringify(results, null, 2));

    const crit = results.violations.filter((v) => v.impact === "critical").length;
    const ser = results.violations.filter((v) => v.impact === "serious").length;
    console.log(`[AXE] requests_list: ${results.violations.length} violations (${crit} critical, ${ser} serious)`);
  });

  test("Scan Screen 3: New Request Form (/requests/new)", async ({ page }) => {
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("alice@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.goto("/requests/new");
    await expect(page).toHaveURL(/\/requests\/new$/);
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page }).analyze();
    fs.writeFileSync(path.join(outputDir, "new_request.json"), JSON.stringify(results, null, 2));

    const crit = results.violations.filter((v) => v.impact === "critical").length;
    const ser = results.violations.filter((v) => v.impact === "serious").length;
    console.log(`[AXE] new_request: ${results.violations.length} violations (${crit} critical, ${ser} serious)`);
  });

  test("Scan Screen 4: Request Detail (/requests/:id)", async ({ page, request }) => {
    const reqId = await prepareRequestDetail(request);

    await page.goto("/login");
    await page.locator('input[type="email"]').fill("fiona@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.goto(`/requests/${reqId}`);
    await expect(page).toHaveURL(new RegExp(`/requests/${reqId}$`));
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page }).analyze();
    fs.writeFileSync(path.join(outputDir, "request_detail.json"), JSON.stringify(results, null, 2));

    const crit = results.violations.filter((v) => v.impact === "critical").length;
    const ser = results.violations.filter((v) => v.impact === "serious").length;
    console.log(`[AXE] request_detail: ${results.violations.length} violations (${crit} critical, ${ser} serious)`);
  });
});
