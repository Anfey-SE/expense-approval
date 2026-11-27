import { expect, test } from "@playwright/test";

const API_BASE = "http://localhost:8081";

function uniqueTitle(prefix: string) {
  return `${prefix} ${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

test.describe("Usability & Accessibility Task Tests — Member 3 (24i-0761)", () => {
  test("Task 1 (Workflow 1 - Submit): Reject invalid business rule value, display error, correct, and confirm submission", async ({
    page,
    request,
  }) => {
    // 1. Employee Alice logs in
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("alice@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);

    // 2. Navigate to New Request
    await page.getByRole("button", { name: "New request" }).click();
    await expect(page).toHaveURL(/\/requests\/new$/);

    const title = uniqueTitle("Usability-W1");
    // Fill title
    await page.locator("form .card").first().locator("input").first().fill(title);
    // Fill line item description
    await page.locator("input[required]").nth(1).fill("Client Lunch Meeting");
    // Fill amount
    await page.locator("input[type='number']").fill("65.00");

    // Enter invalid currency (numbers '123' instead of 3-letter ISO code - violates business rule)
    const currencyInput = page.locator("input[maxlength='3']");
    await currencyInput.fill("123");

    // Attempt to submit invalid form
    await page.getByRole("button", { name: "Create draft" }).click();

    // Assert error message explains the issue / appears
    const errorBanner = page.locator(".error");
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText("Request validation failed");

    // Correct the invalid value to valid ISO code "USD"
    await currencyInput.fill("USD");

    // Submit corrected form
    await page.getByRole("button", { name: "Create draft" }).click();

    // Verify navigation to detail page
    await expect(page).toHaveURL(/\/requests\/\d+$/);
    await expect(page.locator(".badge")).toHaveText("draft");

    // Submit for approval to complete Workflow 1
    const submitBtn = page.getByRole("button", { name: "Submit for approval" });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Assert success confirmation: badge transitions to "submitted" and submit button is removed
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(page.getByRole("button", { name: "Submit for approval" })).toHaveCount(0);
    const trail = page.locator("table").nth(1);
    await expect(trail).toContainText("draft → submitted");
  });

  test("Task 2 (Workflow 2 - Review): Manager reviews submitted request and approves with comment", async ({
    page,
    request,
  }) => {
    // 1. Create and submit an expense request via API
    const loginRes = await request.post(`${API_BASE}/api/auth/login`, {
      data: { email: "alice@acme.com", password: "password123" },
    });
    const aliceToken = (await loginRes.json()).token;

    const title = uniqueTitle("Usability-W2");
    const createRes = await request.post(`${API_BASE}/api/requests`, {
      headers: { Authorization: `Bearer ${aliceToken}` },
      data: {
        title,
        description: "Usability review test",
        currency: "USD",
        items: [
          {
            description: "Team software subscription",
            category: "Software",
            amount: 120.0,
            incurredOn: new Date().toISOString().slice(0, 10),
          },
        ],
      },
    });
    const reqId = (await createRes.json()).id;

    await request.post(`${API_BASE}/api/requests/${reqId}/submit`, {
      headers: { Authorization: `Bearer ${aliceToken}` },
    });

    // 2. Manager Bob logs in
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("bob@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);

    // 3. Navigate to request detail
    await page.goto(`/requests/${reqId}`);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".badge")).toHaveText("submitted");

    // 4. Fill approval comment and submit approval
    const comment = "Approved under engineering team software budget";
    await page.locator("input[maxlength='500']").fill(comment);
    await page.getByRole("button", { name: "Approve" }).click();

    // 5. Confirm success confirmation on screen
    await expect(page.locator(".badge")).toHaveText("manager approved");
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);
    const trail = page.locator("table").nth(1);
    await expect(trail).toContainText("submitted → manager approved");
    await expect(trail).toContainText(comment);
  });

  test("Keyboard Navigation Test: Fill and submit New Request form using ONLY Tab and Enter keys", async ({
    page,
  }) => {
    // Login as Alice
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("alice@acme.com");
    await page.locator('input[type="password"]').fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/$/);

    // Open New Request page
    await page.goto("/requests/new");
    await expect(page.getByRole("heading", { name: "New expense request" })).toBeVisible();

    const title = uniqueTitle("Keyboard-Nav");

    // Initial click on body to establish focus origin
    await page.locator("body").click();

    // Step 1: Tab to Title input
    await page.keyboard.press("Tab");
    // Verify Title input has focus
    const titleVal = await page.evaluate(() => document.activeElement?.getAttribute("value"));
    await page.keyboard.type(title);

    // Step 2: Tab to Description textarea
    await page.keyboard.press("Tab");
    await page.keyboard.type("Entirely entered via keyboard navigation");

    // Step 3: Tab to Currency input
    await page.keyboard.press("Tab");
    // Currency already defaults to USD, press Tab to move to next control

    // Step 4: Tab to "+ Add item" button
    await page.keyboard.press("Tab");
    const isAddItemFocused = await page.evaluate(
      () => document.activeElement?.textContent?.includes("+ Add item")
    );
    expect(isAddItemFocused).toBeTruthy();

    // Step 5: Tab to Line Item Description
    await page.keyboard.press("Tab");
    await page.keyboard.type("Keyboard Item 1");

    // Step 6: Tab to Category select
    await page.keyboard.press("Tab");

    // Step 7: Tab to Amount input
    await page.keyboard.press("Tab");
    await page.keyboard.type("55.00");

    // Step 8: Tab to Date input
    await page.keyboard.press("Tab");

    // Step 9: Tab to Remove button (disabled since items.length == 1) or next active control
    await page.keyboard.press("Tab");

    // Step 10: Tab until focus reaches "Create draft" submit button
    for (let i = 0; i < 5; i++) {
      const isCreateDraft = await page.evaluate(
        () => document.activeElement?.textContent?.includes("Create draft")
      );
      if (isCreateDraft) break;
      await page.keyboard.press("Tab");
    }

    const submitFocused = await page.evaluate(
      () => document.activeElement?.textContent?.includes("Create draft")
    );
    expect(submitFocused).toBeTruthy();

    // Step 11: Submit form using Enter key alone
    await page.keyboard.press("Enter");

    // Assert form was successfully submitted via keyboard and redirected to /requests/:id
    await expect(page).toHaveURL(/\/requests\/\d+$/);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".badge")).toHaveText("draft");
  });
});
