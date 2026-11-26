import { defineConfig } from "@playwright/test";

/**
 * Playwright config for UC1 / UC2 E2E tests.
 *
 * Expects:
 *   - Spring Boot backend running on http://localhost:8081
 *   - Vite dev server running on http://localhost:5173 (proxies /api → :8081)
 *
 * Start them manually before running tests:
 *   cd <repo>            && ./mvnw spring-boot:run
 *   cd <repo>/frontend   && npm run dev
 *
 * Or on CI, use a service container for Postgres and start both in a workflow step.
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
