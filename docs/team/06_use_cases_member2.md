# Use Case Specifications — Member 2 (24i-3097)

**Module:** Expense Requests — Workflow 2 (Review Expense Request: Manager Stage)  
**Automated Suite:** [`tests/team/e2e/test_uc3_uc4_manager_review.py`](../../tests/team/e2e/test_uc3_uc4_manager_review.py)

---

## UC3 — Manager Approves a Submitted Expense Request

| Field | Specification |
|---|---|
| **Use Case ID** | UC3 |
| **Title** | Manager approves a submitted expense request |
| **Primary Actor** | Manager (`MANAGER` role, e.g., `bob@acme.com`, Engineering) |
| **Preconditions** | 1. An `ExpenseRequest` exists in status `SUBMITTED` belonging to the manager's department.<br>2. The manager is not the requester of that expense request.<br>3. The manager is authenticated in the web UI. |
| **Postconditions** | 1. Request `status` transitions from `SUBMITTED` to `MANAGER_APPROVED`.<br>2. An immutable `Approval` record (`action=APPROVE`, `fromStatus=SUBMITTED`, `toStatus=MANAGER_APPROVED`, `actor=Manager`) is appended to the approval trail.<br>3. The request leaves the manager's "Awaiting your approval" inbox and is queued for `FINANCE` review. |

### Main Flow (UC3-MF)
1. Manager signs in at `/login` and lands on `/` (`RequestList`).
2. Manager opens a `SUBMITTED` request from their department (`/requests/{id}`).
3. Manager reviews the line items, total amount, and requester details.
4. Manager clicks **Approve**.
5. System sends `POST /api/requests/{id}/approve`, transitions status to `MANAGER_APPROVED`, appends an `APPROVE` trail row, and updates the UI badge to `manager approved`.

### Alternative Flows
- **UC3-AF1 (Approve with comment):** At step 3, manager enters a comment (e.g., `"Approved within Q4 travel budget"`, up to 500 chars) in `Comment (optional)` before clicking **Approve**. The comment is persisted and displayed in the Approval Trail table.
- **UC3-AF2 (Approve directly from inbox among multiple pending requests):** At step 2, instead of opening `/requests/{id}`, manager clicks **Approve** directly on one row in the **"Awaiting your approval"** table on `/`. That request transitions to `MANAGER_APPROVED` and disappears from the inbox while other `SUBMITTED` requests remain pending.

### Exception Flows
- **UC3-EF1 (Cross-department manager denied):** A manager from another department (e.g., `dave@acme.com`, Sales) navigates to `/requests/{id}` of an Engineering request. System returns HTTP 404 (`Request not found`) to prevent cross-department enumeration; UI displays `"Request not found"`. Postcondition: request remains `SUBMITTED`.
- **UC3-EF2 (Request not in `SUBMITTED` state or self-approval attempted):** Manager opens a request that is `DRAFT`, already `MANAGER_APPROVED`, or submitted by the manager themselves (`isOwner == true`). The `Actions` panel (**Approve** / **Reject**) is not rendered; direct API calls are rejected with HTTP 409 (`NOT_PENDING`) or HTTP 403 (`FORBIDDEN`). Postcondition: status and trail remain unchanged.

### Automation Mapping
- `test_uc3_main_and_alt1_approve_with_comment` -> UC3-MF + UC3-AF1
- `test_uc3_alt2_approve_from_inbox_among_multiple` -> UC3-AF2
- `test_uc3_exc1_cross_department_manager_denied` -> UC3-EF1
- `test_uc3_exc2_not_submitted_and_self_approval_blocked` -> UC3-EF2

---

## UC4 — Manager Rejects a Submitted Expense Request

| Field | Specification |
|---|---|
| **Use Case ID** | UC4 |
| **Title** | Manager rejects a submitted expense request |
| **Primary Actor** | Manager (`MANAGER` role, e.g., `bob@acme.com`, Engineering) |
| **Secondary Actor** | Employee (`EMPLOYEE` role, e.g., `alice@acme.com`) viewing the outcome |
| **Preconditions** | 1. An `ExpenseRequest` exists in status `SUBMITTED` belonging to the manager's department.<br>2. The manager is not the requester.<br>3. The manager is authenticated in the web UI. |
| **Postconditions** | 1. Request `status` transitions from `SUBMITTED` to `REJECTED` (terminal state).<br>2. An immutable `Approval` record (`action=REJECT`, `fromStatus=SUBMITTED`, `toStatus=REJECTED`, `actor=Manager`) is appended to the approval trail.<br>3. The employee can view the `REJECTED` status and manager comment on `/requests/{id}`. |

### Main Flow (UC4-MF)
1. Manager signs in and opens a `SUBMITTED` request in their department (`/requests/{id}`).
2. Manager enters a rejection reason (e.g., `"Receipt missing for meal"`) in `Comment (optional)`.
3. Manager clicks **Reject**.
4. System sends `POST /api/requests/{id}/reject`, sets status to `REJECTED`, appends the `REJECT` trail row, and displays the `rejected` badge and comment.

### Alternative Flows
- **UC4-AF1 (Reject directly from approval inbox):** On `/`, manager clicks **Reject** on a pending row in **"Awaiting your approval"**, enters `"Over meal cap"` in the browser `window.prompt` dialog, and confirms. The request transitions to `REJECTED` and is removed from the inbox.
- **UC4-AF2 (Employee views rejection outcome):** After rejection, the employee (`alice@acme.com`) signs in, opens `/requests/{id}`, and verifies the `rejected` badge and the manager's rejection reason in the Approval Trail.

### Exception Flows
- **UC4-EF1 (Reject without entering a reason):** Manager clicks **Reject** with an empty comment field. Currently the application permits blank rejection comments (`""` stored, rendered as `—` in the trail). This is recorded as Endpoint Weakness **EW-2** and Risk **PR-04**; the test verifies the observed behavior and persisted trail row.
- **UC4-EF2 (Reject an already approved or finalised request):** Manager opens a request in `MANAGER_APPROVED` (or `REJECTED`) status. The **Reject** button is not rendered; direct API calls return HTTP 409 (`NOT_PENDING`) or HTTP 403 (`FORBIDDEN`). Postcondition: status and trail remain unchanged.

### Automation Mapping
- `test_uc4_main_and_alt2_reject_and_employee_views_outcome` -> UC4-MF + UC4-AF2
- `test_uc4_alt1_reject_from_inbox_with_prompt` -> UC4-AF1
- `test_uc4_exc1_reject_without_reason_allowed` -> UC4-EF1
- `test_uc4_exc2_cannot_reject_already_approved_request` -> UC4-EF2
