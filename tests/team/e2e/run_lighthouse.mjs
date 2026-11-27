import lighthouse from "lighthouse";
import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = "http://localhost:5173";
const API_BASE = "http://localhost:8081";

const targetDirName = process.argv[2] || "before";
const outputDir = path.resolve(__dirname, "../../../evidence/m3/lighthouse", targetDirName);
fs.mkdirSync(outputDir, { recursive: true });

async function getAuthToken(email, password = "password123") {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Auth failed for ${email}`);
  const data = await res.json();
  return data.token;
}

async function prepareRequestDetail() {
  const aliceToken = await getAuthToken("alice@acme.com");

  const createRes = await fetch(`${API_BASE}/api/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${aliceToken}`,
    },
    body: JSON.stringify({
      title: `Lighthouse Test ${Date.now()}`,
      description: "Lighthouse audit expense item",
      currency: "USD",
      items: [
        {
          description: "Conference Pass",
          category: "Other",
          amount: 150.0,
          incurredOn: new Date().toISOString().slice(0, 10),
        },
      ],
    }),
  });
  const reqId = (await createRes.json()).id;

  await fetch(`${API_BASE}/api/requests/${reqId}/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${aliceToken}` },
  });

  const bobToken = await getAuthToken("bob@acme.com");
  await fetch(`${API_BASE}/api/requests/${reqId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${bobToken}`,
    },
    body: JSON.stringify({ comment: "Bob approved" }),
  });

  return `${BASE_URL}/requests/${reqId}`;
}

async function run() {
  console.log(`Starting Lighthouse Audits (${targetDirName}) -> ${outputDir}`);

  const detailUrl = await prepareRequestDetail();

  const screens = [
    { name: "login", url: `${BASE_URL}/login` },
    { name: "requests_list", url: `${BASE_URL}/`, email: "alice@acme.com" },
    { name: "new_request", url: `${BASE_URL}/requests/new`, email: "alice@acme.com" },
    { name: "request_detail", url: detailUrl, email: "fiona@acme.com" },
  ];

  let summaryMd = `# Lighthouse Audit Summary (${targetDirName})\n\n`;
  summaryMd += `| Screen | Accessibility | Best Practices | SEO |\n`;
  summaryMd += `|---|---|---|---|\n`;

  const scores = {};

  for (let i = 0; i < screens.length; i++) {
    const s = screens[i];
    const cdpPort = 9222 + i;
    const userDataDir = path.join(os.tmpdir(), `pw-lh-${targetDirName}-${s.name}-${Date.now()}`);

    console.log(`Auditing ${s.name} at ${s.url} (CDP Port: ${cdpPort})...`);
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: true,
      args: [`--remote-debugging-port=${cdpPort}`],
    });

    const page = context.pages()[0] || (await context.newPage());

    if (s.email) {
      const token = await getAuthToken(s.email);
      await page.goto(`${BASE_URL}/login`);
      await page.evaluate((t) => localStorage.setItem("expense.token", t), token);
    }

    await page.goto(s.url);
    await page.waitForLoadState("networkidle");

    const runnerResult = await lighthouse(s.url, {
      port: cdpPort,
      onlyCategories: ["accessibility", "best-practices", "seo"],
      output: ["html", "json"],
      logLevel: "error",
      disableStorageReset: true,
    });

    const lhr = runnerResult.lhr;
    const a11yScore = Math.round((lhr.categories.accessibility?.score || 0) * 100);
    const bpScore = Math.round((lhr.categories["best-practices"]?.score || 0) * 100);
    const seoScore = Math.round((lhr.categories.seo?.score || 0) * 100);

    scores[s.name] = { a11y: a11yScore, bestPractices: bpScore, seo: seoScore };

    fs.writeFileSync(path.join(outputDir, `${s.name}.report.html`), runnerResult.report[0]);
    fs.writeFileSync(path.join(outputDir, `${s.name}.report.json`), runnerResult.report[1]);

    summaryMd += `| \`${s.name}\` | **${a11yScore}** | **${bpScore}** | **${seoScore}** |\n`;
    console.log(
      `[LIGHTHOUSE] ${s.name} -> Accessibility: ${a11yScore}, Best Practices: ${bpScore}, SEO: ${seoScore}`
    );

    await context.close();
  }

  fs.writeFileSync(path.join(outputDir, "summary.md"), summaryMd);
  fs.writeFileSync(path.join(outputDir, "scores.json"), JSON.stringify(scores, null, 2));
  console.log(`Summary written to ${path.join(outputDir, "summary.md")}`);
}

run().catch((err) => {
  console.error("Lighthouse error:", err);
  process.exit(1);
});
