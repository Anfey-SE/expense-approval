import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = "http://host.docker.internal:5173";
const ZAP_PROXY = "http://localhost:8080";
const outputDir = path.resolve(__dirname, "../../../evidence/m3/zap");
fs.mkdirSync(outputDir, { recursive: true });

async function waitForPassiveScan() {
  console.log("Waiting for ZAP passive scan queue to empty...");
  for (let i = 0; i < 60; i++) {
    try {
      const res = await fetch(`${ZAP_PROXY}/JSON/pscan/view/recordsToScan/`);
      const data = await res.json();
      const records = parseInt(data.recordsToScan, 10);
      console.log(`Passive scan queue records remaining: ${records}`);
      if (records === 0) {
        console.log("Passive scan queue is empty!");
        return;
      }
    } catch (e) {
      console.log(`Error checking pscan queue: ${e.message}`);
    }
    await new Promise((r) => setTimeout(r, 1500));
  }
}

async function exportReports() {
  console.log("Exporting ZAP reports...");
  // HTML report
  const htmlRes = await fetch(`${ZAP_PROXY}/OTHER/core/other/htmlreport/`);
  const htmlText = await htmlRes.text();
  fs.writeFileSync(path.join(outputDir, "zap-report.html"), htmlText);
  console.log(`Saved HTML report to ${path.join(outputDir, "zap-report.html")}`);

  // JSON report
  const jsonRes = await fetch(`${ZAP_PROXY}/OTHER/core/other/jsonreport/`);
  const jsonText = await jsonRes.text();
  fs.writeFileSync(path.join(outputDir, "zap-report.json"), jsonText);
  console.log(`Saved JSON report to ${path.join(outputDir, "zap-report.json")}`);

  // Alerts summary
  const alertsRes = await fetch(`${ZAP_PROXY}/JSON/core/view/alerts/`);
  const alertsData = await alertsRes.json();
  const alerts = alertsData.alerts || [];

  const summary = {
    total: alerts.length,
    high: alerts.filter((a) => a.risk === "High").length,
    medium: alerts.filter((a) => a.risk === "Medium").length,
    low: alerts.filter((a) => a.risk === "Low").length,
    informational: alerts.filter((a) => a.risk === "Informational").length,
    items: alerts.map((a) => ({
      risk: a.risk,
      confidence: a.confidence,
      name: a.name,
      url: a.url,
      cweId: a.cweid,
      solution: a.solution,
    })),
  };

  fs.writeFileSync(
    path.join(outputDir, "alerts-summary.json"),
    JSON.stringify(summary, null, 2)
  );

  let md = `# OWASP ZAP Passive Scan Report Summary\n\n`;
  md += `- **Scan Mode:** Passive Proxy (Zero active attacks, purely traffic inspection)\n`;
  md += `- **Total Alerts:** ${summary.total}\n`;
  md += `- **High Risk:** ${summary.high}\n`;
  md += `- **Medium Risk:** ${summary.medium}\n`;
  md += `- **Low Risk:** ${summary.low}\n`;
  md += `- **Informational:** ${summary.informational}\n\n`;
  md += `## Distinct Alert Categories\n\n`;
  md += `| Risk Level | Alert Name | Count | CWE ID |\n`;
  md += `|---|---|---|---|\n`;

  const grouped = {};
  for (const a of summary.items) {
    const key = `${a.risk}:::${a.name}:::${a.cweId}`;
    grouped[key] = (grouped[key] || 0) + 1;
  }
  for (const [k, count] of Object.entries(grouped)) {
    const [risk, name, cwe] = k.split(":::");
    md += `| **${risk}** | ${name} | ${count} | CWE-${cwe} |\n`;
  }

  fs.writeFileSync(path.join(outputDir, "summary.md"), md);
  console.log(`Summary written to ${path.join(outputDir, "summary.md")}`);
}

async function run() {
  console.log(`Launching Playwright with proxy ${ZAP_PROXY}...`);
  const browser = await chromium.launch({
    headless: true,
    proxy: { server: ZAP_PROXY },
    args: [`--proxy-server=${ZAP_PROXY}`, "--proxy-bypass-list="],
  });

  const page = await browser.newPage();

  // Workflow 1: Employee creates draft & submits
  console.log("Driving Workflow 1 through ZAP proxy...");
  await page.goto(`${BASE_URL}/login`);
  await page.locator('input[type="email"]').fill("alice@acme.com");
  await page.locator('input[type="password"]').fill("password123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(new RegExp(`${BASE_URL}/?$`));

  await page.getByRole("link", { name: "New request" }).click();
  await page.waitForURL(new RegExp(`${BASE_URL}/requests/new`));
  await page.locator('#request-title').fill(`ZAP Scan W1 ${Date.now()}`);
  await page.locator('#item-desc-0').fill('Client Dinner');
  await page.locator('input[type="number"]').fill("120.00");
  await page.getByRole("button", { name: "Create draft" }).click();
  await page.waitForURL(new RegExp(`${BASE_URL}/requests/\\d+`));

  await page.getByRole("button", { name: "Submit for approval" }).click();
  await page.waitForSelector(".status-badge, body:has-text('submitted')");
  const reqUrl = page.url();
  console.log(`Submitted request at: ${reqUrl}`);

  // Logout Alice
  await page.getByRole("button", { name: "Log out" }).click();
  await page.waitForURL(`${BASE_URL}/login`);

  // Workflow 2: Manager reviews & approves
  console.log("Driving Workflow 2 (Manager review) through ZAP proxy...");
  await page.locator('input[type="email"]').fill("bob@acme.com");
  await page.locator('input[type="password"]').fill("password123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(new RegExp(`${BASE_URL}`));

  if (page.url() !== reqUrl) {
    await page.goto(reqUrl);
  }
  await page.locator("input[maxlength='500']").fill("Bob approved via ZAP proxy");
  await page.getByRole("button", { name: "Approve" }).click();
  await page.waitForSelector(".status-badge, body:has-text('manager approved')");

  // Logout Bob
  await page.getByRole("button", { name: "Log out" }).click();
  await page.waitForURL(`${BASE_URL}/login`);

  // Workflow 2 part 2: Finance reviews & approves
  console.log("Driving Workflow 2 (Finance review) through ZAP proxy...");
  await page.locator('input[type="email"]').fill("fiona@acme.com");
  await page.locator('input[type="password"]').fill("password123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(new RegExp(`${BASE_URL}`));

  if (page.url() !== reqUrl) {
    await page.goto(reqUrl);
  }
  await page.locator("input[maxlength='500']").fill("Fiona approved via ZAP proxy");
  await page.getByRole("button", { name: "Approve" }).click();
  await page.waitForSelector(".status-badge, body:has-text('finance approved')");

  await browser.close();
  console.log("Workflows completed.");

  await waitForPassiveScan();
  await exportReports();
}

run().catch((err) => {
  console.error("ZAP runner error:", err);
  process.exit(1);
});
