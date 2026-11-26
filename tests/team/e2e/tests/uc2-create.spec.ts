import { expect, test } from "@playwright/test";
import {
  createDraftViaUI,
  fieldByLabel,
  fillNewRequestForm,
  itemRow,
  login,
  uniqueTitle,
} from "./helpers";

test.describe("UC2 — Employee creates a draft with line items", () => {
  test("UC2_M_create_draft_one_item: Alice creates a draft with 1 item", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC2-M");
    await login(page, "alice@acme.com");

    const id = await createDraftViaUI(page, {
      title,
      description: "Client dinner",
      currency: "USD",
      items: [{ description: "Dinner bill", category: "Meals", amount: "64.25" }],
    });

    // Displayed result
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".badge")).toHaveText("draft");
    await expect(page.locator("table").first()).toContainText("USD 64.25");

    // Postcondition: read back independently via API using browser's JWT
    const token = await page.evaluate(() => localStorage.getItem("expense.token"));
    const res = await request.get(`http://localhost:8081/api/requests/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("DRAFT");
    expect(body.title).toBe(title);
    expect(body.totalAmount).toBe(64.25);
    expect(body.items).toHaveLength(1);
  });

  test("UC2_A1_add_remove_items: Add items, remove one, check live Total", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC2-A1");
    await login(page, "alice@acme.com");
    await page.getByRole("button", { name: "New request" }).click();
    await expect(page).toHaveURL(/\/requests\/new$/);

    await fillNewRequestForm(page, {
      title,
      items: [
        { description: "Taxi", category: "Travel", amount: "50.00" },
        { description: "Coffee", category: "Meals", amount: "30.00" },
        { description: "Cable", category: "Supplies", amount: "20.00" },
      ],
    });

    await expect(page.getByText("Total: USD 100.00")).toBeVisible();

    // Remove the second item (Coffee, 30.00)
    await itemRow(page, 1).getByTitle("Remove").click();
    await expect(page.getByText("Total: USD 70.00")).toBeVisible();

    await page.getByRole("button", { name: "Create draft" }).click();
    await expect(page).toHaveURL(/\/requests\/(\d+)$/);
    const id = page.url().match(/\/requests\/(\d+)$/)![1];

    // Displayed result
    await expect(page.locator(".badge")).toHaveText("draft");
    await expect(page.locator("table").first()).toContainText("USD 70.00");

    // Postcondition: independent API read-back
    const token = await page.evaluate(() => localStorage.getItem("expense.token"));
    const res = await request.get(`http://localhost:8081/api/requests/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.items).toHaveLength(2);
    expect(body.totalAmount).toBe(70);
  });

  test("UC2_A2_remove_button_disabled: Remove button disabled when only 1 item left", async ({
    page,
  }) => {
    const uniqueMarker = uniqueTitle("UC2-A2-NOSUBMIT");
    await login(page, "alice@acme.com");
    await page.getByRole("button", { name: "New request" }).click();

    await fieldByLabel(page.locator("form .card").first(), "Title").fill(uniqueMarker);
    const firstRemove = itemRow(page, 0).getByTitle("Remove");
    await expect(firstRemove).toBeDisabled();

    await page.getByRole("button", { name: "+ Add item" }).click();
    await expect(itemRow(page, 0).getByTitle("Remove")).toBeEnabled();
    await expect(itemRow(page, 1).getByTitle("Remove")).toBeEnabled();

    await itemRow(page, 1).getByTitle("Remove").click();
    await expect(firstRemove).toBeDisabled();

    // Postcondition: nothing created
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "My requests" })).toBeVisible();
    await expect(page.getByText(uniqueMarker)).toHaveCount(0);
  });

  test("UC2_E1_blank_title: Blank title prevents submission and creates nothing", async ({
    page,
  }) => {
    const uniqueItemDesc = uniqueTitle("UC2-E1-ITEM");
    await login(page, "alice@acme.com");
    await page.getByRole("button", { name: "New request" }).click();

    await fillNewRequestForm(page, {
      title: "",
      items: [{ description: uniqueItemDesc, category: "Other", amount: "15.00" }],
    });

    await page.getByRole("button", { name: "Create draft" }).click();

    // Displayed result: still on /requests/new (HTML5 required blocks submit)
    await expect(page).toHaveURL(/\/requests\/new$/);

    // Postcondition: list has no newly created request with this item/empty title
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "My requests" })).toBeVisible();
    await expect(page.getByText(uniqueItemDesc)).toHaveCount(0);
  });

  test("UC2_E2_invalid_currency: Currency 123 shows error div and creates nothing", async ({
    page,
  }) => {
    const title = uniqueTitle("UC2-E2");
    await login(page, "alice@acme.com");
    await page.getByRole("button", { name: "New request" }).click();

    await fillNewRequestForm(page, {
      title,
      currency: "123",
      items: [{ description: "USB hub", category: "Supplies", amount: "25.00" }],
    });

    await page.getByRole("button", { name: "Create draft" }).click();

    // Displayed result
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.locator(".error")).toHaveText("Request validation failed");

    // Postcondition: no request created
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "My requests" })).toBeVisible();
    await expect(page.getByText(title)).toHaveCount(0);
  });
});
