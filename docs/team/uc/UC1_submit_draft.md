# UC1 — Employee submits a draft for approval

| Field | Value |
|---|---|
| **ID** | UC1 |
| **Name** | Submit a draft for approval |
| **Actor** | Employee (Alice Employee, `alice@acme.com`) |
| **Goal** | Move an existing DRAFT expense request to SUBMITTED so it enters the approval workflow |
| **Related BRs** | BR1 (state machine: DRAFT → SUBMITTED), BR3 (employees see only their own requests) |

## Preconditions

1. The employee is logged in.
2. A DRAFT expense request exists, owned by the employee, with at least one line item.

## Trigger

The employee navigates to the detail page of a DRAFT request and clicks **"Submit for approval"**.

## Postconditions (success)

1. The request's status is **SUBMITTED** (visible on screen and confirmed via API reload).
2. The approval trail shows a **SUBMIT** entry with `draft → submitted` transition.
3. The **"Submit for approval"** button is no longer visible.

---

## Main Flow — UC1_M

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice logs in and creates a draft with 1 item | Draft created, redirected to `/requests/{id}` |
| 2 | On the detail page, click **"Submit for approval"** | Status badge changes to **submitted** |
| 3 | Approval trail table appears | Shows one row: action = SUBMIT, transition = draft → submitted |
| 4 | **Postcondition check**: reload the page | Status is still SUBMITTED; button is gone |

**Playwright test**: `UC1_M_submit_draft`

---

## Alternative Flow 1 — UC1_A1: Submit with 3 items from different categories

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice creates a draft with 3 items (Travel, Meals, Supplies) | Draft created with correct total |
| 2 | Verify line items table shows all 3 rows, with correct descriptions and amounts | All items displayed |
| 3 | Verify total equals sum of the 3 amounts | Total matches |
| 4 | Click **"Submit for approval"** | Status changes to submitted |
| 5 | Approval trail shows SUBMIT row | Transition: draft → submitted |
| 6 | **Postcondition check**: reload and verify status + total via page content | Still SUBMITTED, total unchanged |

**Playwright test**: `UC1_A1_submit_three_items`

---

## Alternative Flow 2 — UC1_A2: Create a draft and do not submit

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice creates a draft with 1 item | Draft created, redirected to detail page |
| 2 | Status badge shows **draft** | Correct |
| 3 | **"Submit for approval"** button is visible | Button present |
| 4 | Approval trail section shows **"Not submitted yet."** | Correct |
| 5 | **Postcondition check**: reload the page | Status is still DRAFT; button still visible; trail still says "Not submitted yet." |

**Playwright test**: `UC1_A2_draft_not_submitted`

---

## Exception Flow 1 — UC1_E1: Button disappears after submitting

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice creates and submits a draft | Status changes to submitted |
| 2 | Verify **"Submit for approval"** button is NOT visible | Button gone |
| 3 | **Postcondition check**: reload the page | Button still gone; status still SUBMITTED |

**Playwright test**: `UC1_E1_button_gone_after_submit`

---

## Exception Flow 2 — UC1_E2: Cross-user access denied

| Step | Action | Expected result |
|---|---|---|
| 1 | Alice creates a draft (note the request ID from the URL) | Draft created |
| 2 | Log out Alice, log in as Carol (`carol@acme.com`, Sales employee) | Carol logged in |
| 3 | Carol navigates directly to `/requests/{alice's id}` | Error: **"Request not found"** (server returns 404 because employees cannot view other users' requests) |
| 4 | **Postcondition check**: Carol's request list does NOT contain Alice's request | List does not show it |

**Playwright test**: `UC1_E2_cross_user_access_denied`

---

## Flow-to-Test Mapping

| Flow ID | Test name | Asserts display? | Asserts postcondition? |
|---|---|---|---|
| UC1_M | `UC1_M_submit_draft` | ✓ status badge, trail row | ✓ reload page |
| UC1_A1 | `UC1_A1_submit_three_items` | ✓ 3 items, total, trail | ✓ reload page |
| UC1_A2 | `UC1_A2_draft_not_submitted` | ✓ DRAFT badge, button, trail text | ✓ reload page |
| UC1_E1 | `UC1_E1_button_gone_after_submit` | ✓ button absent | ✓ reload page |
| UC1_E2 | `UC1_E2_cross_user_access_denied` | ✓ error message | ✓ Carol's list |
