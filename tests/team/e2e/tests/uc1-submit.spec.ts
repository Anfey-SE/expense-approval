import { expect, test } from "@playwright/test";
import { createDraftViaUI, login, logout, uniqueTitle } from "./helpers";

test.describe("UC1 — Employee submits a draft for approval", () => {
  test("UC1_M_submit_draft: Alice submits a draft and sees SUBMITTED status and trail", async ({
    page,
  }) => {
    const title = uniqueTitle("UC1-M");
    await login(page, "alice@acme.com");
    await createDraftViaUI(page, {
      title,
      description: "Main flow submit test",
      items: [{ description: "Flight ticket", category: "Travel", amount: "125.50" }],
    });

    await expect(page.locator(".badge")).toHaveText("draft");
    await page.getByRole("button", { name: "Submit for approval" }).click();

    // Displayed result
    await expect(page.locator(".badge")).toHaveText("submitted");
    const trailTable = page.locator("table").nth(1);
    await expect(trailTable).toContainText("SUBMIT");
    await expect(trailTable).toContainText("draft → submitted");

    // Postcondition: reload and verify persisted state
    await page.reload();
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(page.getByRole("button", { name: "Submit for approval" })).toHaveCount(0);
    await expect(page.locator("table").nth(1)).toContainText("SUBMIT");
  });

  test("UC1_A1_submit_three_items: Submit draft with 3 items from different categories", async ({
    page,
  }) => {
    const title = uniqueTitle("UC1-A1");
    await login(page, "alice@acme.com");
    await createDraftViaUI(page, {
      title,
      items: [
        { description: "Train fare", category: "Travel", amount: "45.00" },
        { description: "Team lunch", category: "Meals", amount: "32.50" },
        { description: "Notebooks", category: "Supplies", amount: "12.50" },
      ],
    });

    const itemsTable = page.locator("table").first();
    await expect(itemsTable).toContainText("Train fare");
    await expect(itemsTable).toContainText("Team lunch");
    await expect(itemsTable).toContainText("Notebooks");
    await expect(itemsTable).toContainText("USD 90.00");

    await page.getByRole("button", { name: "Submit for approval" }).click();

    // Displayed result
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(page.locator("table").nth(1)).toContainText("SUBMIT");

    // Postcondition: reload and verify total + status persisted
    await page.reload();
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(page.locator("table").first()).toContainText("USD 90.00");
    await expect(page.locator("table").nth(1)).toContainText("draft → submitted");
  });

  test("UC1_A2_draft_not_submitted: Create draft and do not submit", async ({ page }) => {
    const title = uniqueTitle("UC1-A2");
    await login(page, "alice@acme.com");
    await createDraftViaUI(page, {
      title,
      items: [{ description: "Hotel night", category: "Lodging", amount: "180.00" }],
    });

    // Displayed result
    await expect(page.locator(".badge")).toHaveText("draft");
    await expect(page.getByRole("button", { name: "Submit for approval" })).toBeVisible();
    await expect(page.getByText("Not submitted yet.")).toBeVisible();

    // Postcondition: reload and verify still DRAFT
    await page.reload();
    await expect(page.locator(".badge")).toHaveText("draft");
    await expect(page.getByRole("button", { name: "Submit for approval" })).toBeVisible();
    await expect(page.getByText("Not submitted yet.")).toBeVisible();
  });

  test("UC1_E1_button_gone_after_submit: Submit button disappears and stays gone on reload", async ({
    page,
  }) => {
    const title = uniqueTitle("UC1-E1");
    await login(page, "alice@acme.com");
    await createDraftViaUI(page, {
      title,
      items: [{ description: "IDE license", category: "Software", amount: "99.00" }],
    });

    const submitBtn = page.getByRole("button", { name: "Submit for approval" });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Displayed result
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(submitBtn).toHaveCount(0);

    // Postcondition: reload and confirm button is still absent
    await page.reload();
    await expect(page.locator(".badge")).toHaveText("submitted");
    await expect(submitBtn).toHaveCount(0);
  });

  test("UC1_E2_cross_user_access_denied: Carol cannot open Alice's request URL", async ({
    page,
  }) => {
    const title = uniqueTitle("UC1-E2");
    await login(page, "alice@acme.com");
    const aliceRequestId = await createDraftViaUI(page, {
      title,
      items: [{ description: "Monitor stand", category: "Supplies", amount: "49.99" }],
    });

    await page.getByRole("link", { name: "← Back to requests" }).click();
    await expect(page).toHaveURL(/\/$/);
    await logout(page);
    await login(page, "carol@acme.com");

    // Carol navigates directly to Alice's request URL
    await page.goto(`/requests/${aliceRequestId}`);

    // Displayed result
    await expect(page.locator(".error")).toHaveText("Request not found");

    // Postcondition: Carol's list does not contain Alice's request
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "My requests" })).toBeVisible();
    await expect(page.getByText(title)).toHaveCount(0);
  });
});
