import { expect, type Locator, type Page } from "@playwright/test";

export const TODAY = new Date().toISOString().slice(0, 10);

export function uniqueTitle(prefix: string): string {
  return `${prefix} ${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

/** Locate an input/textarea/select inside the <div> whose <label> matches `labelText`. */
export function fieldByLabel(scope: Page | Locator, labelText: string): Locator {
  return scope
    .locator("label")
    .filter({ hasText: new RegExp(`^${labelText}$`) })
    .first()
    .locator("..")
    .locator("input, textarea, select");
}

/** Return the Nth line-item row container on the NewRequest form (0-indexed). */
export function itemRow(page: Page, index: number): Locator {
  // Each item row has class "grid2" inside the Line items card.
  return page.locator("form .card .grid2").nth(index);
}

export async function login(page: Page, email: string, password = "password123") {
  await page.goto("/login");
  await fieldByLabel(page, "Email").fill(email);
  await fieldByLabel(page, "Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/$/);
}

export async function logout(page: Page) {
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

export interface ItemSpec {
  description: string;
  category?: string;
  amount: string;
  date?: string;
}

export async function fillNewRequestForm(
  page: Page,
  opts: {
    title?: string;
    description?: string;
    currency?: string;
    items: ItemSpec[];
  }
) {
  // First card holds Title, Description, Currency.
  const headerCard = page.locator("form .card").first();
  if (opts.title !== undefined) {
    await fieldByLabel(headerCard, "Title").fill(opts.title);
  }
  if (opts.description !== undefined) {
    await fieldByLabel(headerCard, "Description").fill(opts.description);
  }
  if (opts.currency !== undefined) {
    await fieldByLabel(headerCard, "Currency").fill(opts.currency);
  }

  for (let i = 0; i < opts.items.length; i++) {
    if (i > 0) {
      await page.getByRole("button", { name: "+ Add item" }).click();
    }
    const row = itemRow(page, i);
    const it = opts.items[i];
    await fieldByLabel(row, "Description").fill(it.description);
    if (it.category) {
      await fieldByLabel(row, "Category").selectOption(it.category);
    }
    await fieldByLabel(row, "Amount").fill(it.amount);
    if (it.date) {
      await fieldByLabel(row, "Date").fill(it.date);
    }
  }
}

/** Create a draft through the UI and return its numeric ID from /requests/{id}. */
export async function createDraftViaUI(
  page: Page,
  opts: {
    title: string;
    description?: string;
    currency?: string;
    items: ItemSpec[];
  }
): Promise<string> {
  await page.getByRole("button", { name: "New request" }).click();
  await expect(page).toHaveURL(/\/requests\/new$/);
  await fillNewRequestForm(page, opts);
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page).toHaveURL(/\/requests\/\d+$/);
  const match = page.url().match(/\/requests\/(\d+)$/);
  if (!match) {
    throw new Error(`Expected /requests/{id} URL, got ${page.url()}`);
  }
  return match[1];
}
