# Use Case Specifications — Member 3 (24i-0761)

**Module:** Expense Requests — Workflow 2 (Review Expense Request: Finance Stage)  
**Automated Suites:** [`tests/team/e2e/tests/uc5-uc6-finance.spec.ts`](../../tests/team/e2e/tests/uc5-uc6-finance.spec.ts) and [`tests/team/e2e/test_uc5_uc6_finance_review.py`](../../tests/team/e2e/test_uc5_uc6_finance_review.py)

---

## UC5 — Finance Approves a Manager-Approved Expense Request

| Field | Specification |
|---|---|
| **Use Case ID** | UC5 |
| **Title** | Finance approves a manager-approved expense request |
| **Primary Actor** | Finance User (`FINANCE` role, e.g., `fiona@acme.com`, Finance) |
| **Preconditions** | 1. An `ExpenseRequest` exists in status `MANAGER_APPROVED`.<br>2. The finance user is not the requester of that expense request (BR4: no self-decision).<br>3. The finance user is authenticated in the web UI. |
| **Postconditions** | 1. Request `status` transitions from `MANAGER_APPROVED` to `FINANCE_APPROVED` (terminal state).<br>2. An immutable `Approval` record (`action=APPROVE`, `fromStatus=MANAGER_APPROVED`, `toStatus=FINANCE_APPROVED`, `actor=Finance`) is appended to the approval trail.<br>3. The request leaves the finance inbox ("Awaiting your approval") and is marked `finance approved` organization-wide. |

### Main Flow (UC5-MF)
1. Finance user signs in at `/login` and lands on `/` (`RequestList`).
2. Finance user opens a `MANAGER_APPROVED` request from any department (`/requests/{id}`).
3. Finance user reviews the line items, total amount, requester name, department, and previous manager approval in the Approval Trail.
4. Finance user clicks **Approve**.
5. System sends `POST /api/requests/{id}/approve`, transitions status to `FINANCE_APPROVED`, appends an `APPROVE` trail row, and updates the UI badge to `finance approved`.

### Alternative Flows
- **UC5-AF1 (Approve with comment):** At step 3, Finance enters a comment (e.g., `"Final Q4 budget approved; payment scheduled"`, up to 500 chars) in `Comment (optional)` before clicking **Approve**. The comment is persisted and displayed in the Approval Trail table.
- **UC5-AF2 (Approve directly from inbox among multiple pending requests):** At step 2, instead of opening `/requests/{id}`, Finance clicks **Approve** directly on one row in the **"Awaiting your approval"** table on `/`. That request transitions to `FINANCE_APPROVED` and disappears from the inbox while other `MANAGER_APPROVED` requests remain pending.

### Exception Flows
- **UC5-EF1 (Attempt approval of request not yet manager-approved):** Finance navigates to `/requests/{id}` of a request in `DRAFT` or `SUBMITTED` status. The **Approve** / **Reject** buttons are not rendered (since `detail.status === "MANAGER_APPROVED"` is required for Finance in `RequestDetail.tsx`); direct API call returns HTTP 409 (`NOT_PENDING`) or HTTP 403 (`FORBIDDEN`). Postcondition: request status and trail remain unchanged.
- **UC5-EF2 (Non-finance user attempt or self-approval attempted):** A non-finance user (e.g., employee `alice@acme.com` or manager `bob@acme.com`), or a finance user who is the requester (`isOwner == true`), attempts to approve a `MANAGER_APPROVED` request. The Actions panel is not rendered; direct API call returns HTTP 403 (`FORBIDDEN`). Postcondition: status and trail remain unchanged.
- **UC5-EF3 (Repeated approval attempt on already finalised request):** A user submits a second approval on a request already in `FINANCE_APPROVED` status. The UI no longer displays the action buttons; direct API call returns HTTP 409 (`NOT_PENDING`), and the approval trail gains zero duplicate rows.

### Automation Mapping
- `test_uc5_main_and_alt1_approve_with_comment` -> UC5-MF + UC5-AF1
- `test_uc5_alt2_approve_from_inbox_among_multiple` -> UC5-AF2
- `test_uc5_exc1_cannot_approve_submitted_or_draft_request` -> UC5-EF1
- `test_uc5_exc2_non_finance_and_self_approval_blocked` -> UC5-EF2
- `test_uc5_exc3_repeated_approval_yields_no_duplicate_trail` -> UC5-EF3

---

## UC6 — Finance Rejects a Manager-Approved Expense Request

| Field | Specification |
|---|---|
| **Use Case ID** | UC6 |
| **Title** | Finance rejects a manager-approved expense request |
| **Primary Actor** | Finance User (`FINANCE` role, e.g., `fiona@acme.com`, Finance) |
| **Secondary Actor** | Employee (`EMPLOYEE` role, e.g., `alice@acme.com`) or Manager (`bob@acme.com`) viewing the rejection outcome |
| **Preconditions** | 1. An `ExpenseRequest` exists in status `MANAGER_APPROVED`.<br>2. The finance user is not the requester.<br>3. The finance user is authenticated in the web UI. |
| **Postconditions** | 1. Request `status` transitions from `MANAGER_APPROVED` to `REJECTED` (terminal state).<br>2. An immutable `Approval` record (`action=REJECT`, `fromStatus=MANAGER_APPROVED`, `toStatus=REJECTED`, `actor=Finance`) is appended to the approval trail.<br>3. The request leaves the finance inbox ("Awaiting your approval") and displays the `rejected` badge and comment. |

### Main Flow (UC6-MF)
1. Finance user signs in and opens a `MANAGER_APPROVED` request (`/requests/{id}`).
2. Finance user enters a rejection reason (e.g., `"Budget cap exceeded for department"`) in `Comment (optional)`.
3. Finance user clicks **Reject**.
4. System sends `POST /api/requests/{id}/reject`, sets status to `REJECTED`, appends the `REJECT` trail row with comment, and displays the `rejected` badge and comment.

### Alternative Flows
- **UC6-AF1 (Reject directly from approval inbox with prompt):** On `/`, Finance clicks **Reject** on a row in **"Awaiting your approval"**, enters reason `"Missing tax invoice"` into the browser `window.prompt` dialog, and confirms. The request transitions to `REJECTED` and is removed from the inbox.
- **UC6-AF2 (Requester and manager view rejection outcome in trail):** After Finance rejects, the employee (`alice@acme.com`) signs in, opens `/requests/{id}`, and confirms the `rejected` badge and the Finance rejection reason in the Approval Trail table (`manager approved → rejected`).

### Exception Flows
- **UC6-EF1 (Reject without entering a reason):** Finance clicks **Reject** with an empty comment field. Currently the application permits blank rejection comments (`""` stored, displayed as `—` in trail). This is recorded as Endpoint Weakness **EW-2** and Risk **PR-04**; the test verifies the observed behavior and persisted trail row.
- **UC6-EF2 (Reject an already finalised or non-pending request):** Finance attempts to reject a request in `FINANCE_APPROVED` or `REJECTED` status. The **Reject** button is not rendered; direct API call returns HTTP 409 (`NOT_PENDING`). Postcondition: status and trail remain unchanged.

### Automation Mapping
- `test_uc6_main_and_alt2_reject_and_employee_views_outcome` -> UC6-MF + UC6-AF2
- `test_uc6_alt1_reject_from_inbox_with_prompt` -> UC6-AF1
- `test_uc6_exc1_reject_without_reason_allowed` -> UC6-EF1
- `test_uc6_exc2_cannot_reject_already_finalised_request` -> UC6-EF2
