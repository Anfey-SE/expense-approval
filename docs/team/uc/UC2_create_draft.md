# UC2 — Employee creates a draft with line items

| Field | Value |
|---|---|
| **ID** | UC2 |
| **Name** | Create a draft expense request with line items |
| **Actor** | Employee (Alice Employee, `alice@acme.com`) |
| **Goal** | Create a new DRAFT expense request with one or more line items via the UI |
| **Related BRs** | BR1 (new requests start as DRAFT), BR3 (employee ownership) |

## Preconditions

1. The employee is logged in.

## Trigger

The employee clicks **"New request"** on the request list page, fills the form, and clicks **"Create draft"**.

## Postconditions (success)

1. A new expense request exists with status **DRAFT**.
2. The employee is redirected to `/requests/{id}` showing the new request.
3. All submitted field values (title, description, currency, items) are reflected on the detail page.
4. The total amount equals the sum of the item amounts.

---

## Main Flow — UC2_M

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice logs in and clicks **"New request"** | Navigated to `/requests/new` |
| 2 | Fill in: Title, Description, Currency (USD), 1 line item (description, category, amount, date) | Form populated |
| 3 | Click **"Create draft"** | Redirected to `/requests/{id}` |
| 4 | Detail page shows: title, status = **draft**, line item table with 1 row, correct total | All correct |
| 5 | **Postcondition check**: use Playwright API request to `GET /api/requests/{id}` | Status = DRAFT, totalAmount matches, item count = 1 |

**Playwright test**: `UC2_M_create_draft_one_item`

---

## Alternative Flow 1 — UC2_A1: Add items, remove one, check live Total

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice opens `/requests/new` | Form shown with 1 default item row |
| 2 | Fill the first item (amount = 50.00) | Total shows `USD 50.00` |
| 3 | Click **"+ Add item"** twice (now 3 rows) | 3 item rows visible |
| 4 | Fill second item (amount = 30.00) and third item (amount = 20.00) | Total updates to `USD 100.00` |
| 5 | Click the **✕** (Remove) button on the second item | 2 rows remain; total updates to `USD 70.00` |
| 6 | Click **"Create draft"** | Redirected to detail page |
| 7 | Detail page shows 2 items with correct total | Correct |
| 8 | **Postcondition check**: API `GET /api/requests/{id}` confirms 2 items, total = 70.00 | Matches |

**Playwright test**: `UC2_A1_add_remove_items`

---

## Alternative Flow 2 — UC2_A2: Remove button disabled when only one item

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice opens `/requests/new` | Form shown with 1 item row |
| 2 | The **✕** (Remove) button is **disabled** | Cannot remove the last item |
| 3 | Click **"+ Add item"** | 2 rows now; both ✕ buttons are **enabled** |
| 4 | Click **✕** on one row | Back to 1 row; ✕ is disabled again |
| 5 | **Postcondition check**: no request was created (this is a form-level check, not a submission) — navigate to list and verify no new request with the test's unique title appears | List does not show it |

**Playwright test**: `UC2_A2_remove_button_disabled`

---

## Exception Flow 1 — UC2_E1: Blank title prevents submission

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice opens `/requests/new` | Form shown |
| 2 | Leave Title empty, fill in 1 valid line item | Title is blank |
| 3 | Click **"Create draft"** | HTML5 validation prevents submission (no network request sent) |
| 4 | **Postcondition check**: navigate to list and verify no new request with an empty title was created | Nothing created |

**Playwright test**: `UC2_E1_blank_title`

---

## Exception Flow 2 — UC2_E2: Invalid currency (digits) shows error

The server-side `@Pattern(regexp = "[A-Za-z]{3}")` annotation on the `currency` field
([ExpenseDtos.java L42](../../../src/main/java/com/sandy/expense/web/dto/ExpenseDtos.java))
rejects non-letter currencies. The frontend's `maxLength={3}` and `.toUpperCase()` do not
block digit-only values.

The error div displays: **"Request validation failed"**

(The per-field message `"currency must be 3 letters"` is captured in `ApiError.fields`
but the UI only renders the top-level `message` — see
[NewRequest.tsx L44](../../../frontend/src/pages/NewRequest.tsx) and
[api.ts L82-84](../../../frontend/src/api.ts).)

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice opens `/requests/new` | Form shown |
| 2 | Fill Title, 1 valid line item, set Currency to **"123"** | Currency field shows "123" |
| 3 | Click **"Create draft"** | Error div appears with text **"Request validation failed"** |
| 4 | **Postcondition check**: navigate to list and verify no new request with the test's unique title was created | Nothing created |

**Playwright test**: `UC2_E2_invalid_currency`

---

## Flow-to-Test Mapping

| Flow ID | Test name | Asserts display? | Asserts postcondition? |
|---|---|---|---|
| UC2_M | `UC2_M_create_draft_one_item` | ✓ detail page content | ✓ API GET |
| UC2_A1 | `UC2_A1_add_remove_items` | ✓ live total, item count | ✓ API GET |
| UC2_A2 | `UC2_A2_remove_button_disabled` | ✓ disabled state | ✓ list page |
| UC2_E1 | `UC2_E1_blank_title` | ✓ form not submitted | ✓ list page |
| UC2_E2 | `UC2_E2_invalid_currency` | ✓ error div text | ✓ list page |
