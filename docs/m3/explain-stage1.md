# Stage 1 Explanation: UC5 & UC6 Specifications and E2E Automation — Member 3 (24i-0761)

## 1. What Was Done
1. **Authored Formal Use Case Specifications:** Wrote [`docs/m3/use-cases.md`](use-cases.md) following the format established by Member 2 in `docs/team/06_use_cases_member2.md`.
   - **UC5:** Finance approves a manager-approved request (Main Flow, 2 Alternative Flows, 3 Exception Flows).
   - **UC6:** Finance rejects a manager-approved request (Main Flow, 2 Alternative Flows, 2 Exception Flows).
2. **Automated Every Flow in Playwright:** Implemented [`tests/team/e2e/tests/uc5-uc6-finance.spec.ts`](../../tests/team/e2e/tests/uc5-uc6-finance.spec.ts) and [`tests/team/e2e/test_uc5_uc6_finance_review.py`](../../tests/team/e2e/test_uc5_uc6_finance_review.py).
3. **Executed Real Test Runs Against Live App:** Ran the full 9-test suite against the live stack (PostgreSQL 16 on port 5433, Spring Boot 4.1 backend on port 8081, React 19 frontend on port 5173).
4. **Resolved Real Locators & Flakiness:** Diagnosed regex parenthetical escaping for the comment field and handled React Router's post-logout redirection state.
5. **Saved Official Evidence Report:** Successfully produced the standalone Playwright HTML report at [`evidence/m3/playwright-uc5-uc6/index.html`](../../evidence/m3/playwright-uc5-uc6/index.html).

---

## 2. Why Each Flow Was Designed and Tested
In the Expense Approval state machine:
- `MANAGER_APPROVED` is the pre-final stage owned exclusively by the `FINANCE` role.
- Approval advances the request to `FINANCE_APPROVED` (terminal success).
- Rejection transitions the request to `REJECTED` (terminal failure).

Testing these transitions ensures:
1. **Stage Ownership & Authorization:** Only accounts with `Role.FINANCE` can act on `MANAGER_APPROVED` requests.
2. **No Self-Decision (BR4):** Even a finance user cannot approve or reject an expense request they submitted themselves.
3. **Audit Trail Immutability (BR3):** Every valid transition appends exactly one immutable audit row to `approvals` (`SUBMIT -> MANAGER_APPROVED -> FINANCE_APPROVED` or `REJECTED`). Disallowed or repeated attempts must never insert duplicate rows.
4. **User Journey & UI Parity:** Approvers can act either from the detailed view (`/requests/{id}`) or directly from their dashboard inbox ("Awaiting your approval").

---

## 3. What Each Automated Test Asserts

| Test Name | Flow Covered | UI Assertions | Postcondition Assertions (API Read-Back) |
|---|---|---|---|
| `UC5_MF_and_AF1_finance_approves_with_comment` | UC5-MF & AF1 | Badge changes to `finance approved`, comment appears in trail, Approve/Reject buttons disappear. | Status `FINANCE_APPROVED`, trail has 3 rows (`SUBMIT`, `APPROVE` by manager, `APPROVE` by finance with comment). |
| `UC5_AF2_finance_approves_from_inbox` | UC5-AF2 | Click Approve on inbox row; target disappears from inbox while sibling remains visible. | Target status is `FINANCE_APPROVED`; sibling remains `MANAGER_APPROVED`. |
| `UC5_EF1_finance_cannot_approve_submitted_or_draft_request` | UC5-EF1 | On `SUBMITTED` request, Approve button is hidden for Finance. | Direct API call rejected with 403/409; status remains `SUBMITTED`, trail count remains 1. |
| `UC5_EF2_non_finance_and_self_approval_blocked` | UC5-EF2 | Employee sees no Approve button; Finance self-request hides decision buttons. | Direct API call by Employee returns HTTP 403; direct API call by Finance on own request returns HTTP 403. |
| `UC5_EF3_repeated_approval_yields_no_duplicate_trail` | UC5-EF3 | Actions panel hidden on finalised request. | Direct repeated API call returns HTTP 409 (`NOT_PENDING`); audit trail contains **zero duplicate rows** (exactly 3 rows). |
| `UC6_MF_and_AF2_finance_rejects_and_employee_views_outcome` | UC6-MF & AF2 | Finance sees `rejected` badge and comment; Employee logs in and views `rejected` badge and manager/finance trail. | Status `REJECTED`, trail length 3, last approval action `REJECT` with reason. |
| `UC6_AF1_finance_rejects_from_inbox_with_prompt` | UC6-AF1 | Browser prompt accepts reason; row disappears from inbox. | Status `REJECTED`, last trail comment matches prompt input. |
| `UC6_EF1_finance_reject_without_reason_allowed` | UC6-EF1 | Finance clicks Reject without comment; UI confirms rejection. | Status `REJECTED`, comment stored as empty string `""` (documents EW-2 / PR-04). |
| `UC6_EF2_cannot_reject_already_finalised_request` | UC6-EF2 | Reject button absent on `FINANCE_APPROVED` request. | Direct API rejection returns HTTP 409 (`NOT_PENDING`); status remains `FINANCE_APPROVED`. |

---

## 4. What Each Tool Output Means
- **`Running 9 tests using 1 worker`:** Playwright executes the tests sequentially in a single headless Chromium worker process to guarantee data isolation and avoid concurrency race conditions on shared demo user accounts.
- **`ok 1 ... (2.6s)`:** The test completed all UI interactions, network requests, DOM assertions, reloads, and independent API read-backs within 2.6 seconds.
- **`9 passed (20.1s)`:** All 9 use case flows passed cleanly with 100% pass rate.
- **`evidence/m3/playwright-uc5-uc6/index.html`:** The generated HTML test report containing step-by-step traces, execution timings, and verification logs.

---

## 5. Five Likely Viva Questions with Short Answers

### Q1: What is the difference between UC3/UC4 (Manager Review) and UC5/UC6 (Finance Review)?
**Answer:** UC3 and UC4 govern the transition from `SUBMITTED` to either `MANAGER_APPROVED` or `REJECTED`. That stage is scoped by department (e.g., Engineering manager only reviews Engineering requests). UC5 and UC6 govern the transition from `MANAGER_APPROVED` to either `FINANCE_APPROVED` or `REJECTED`. The Finance stage is organization-wide and is the final approval required for reimbursement.

### Q2: Why must end-to-end tests assert postconditions via API read-back in addition to checking UI badges?
**Answer:** UI assertions only verify that the client-side state updated in the browser DOM. A client-side bug could optimistically display a "finance approved" badge even if the HTTP write failed or partial data was saved. An independent API read-back (using JWT tokens over HTTP) guarantees that the transaction committed to the PostgreSQL database, the status column updated, and the audit trail gained the exact required row.

### Q3: What prevents a Finance user from approving their own expense requests (BR4)?
**Answer:** Defense in depth:
1. In the React UI, `canDecide` checks `!isOwner` (`user.id !== detail.requesterId`), hiding the Actions card.
2. In the Spring backend, `ExpenseService.assertCanDecide` verifies `if (r.getRequester().getId().equals(me.getUserId())) throw ApiException.forbidden(...)`, returning HTTP 403 even if a user bypasses the UI and calls the REST endpoint directly.

### Q4: What is Endpoint Weakness EW-2 / Risk PR-04 observed in UC6-EF1?
**Answer:** When rejecting an expense request, business best practice requires an explanatory reason so the employee knows why their reimbursement was declined. However, `POST /api/requests/{id}/reject` accepts an empty or omitted comment without validation. The test records this genuine weakness (persisting `""` which renders as `—` in the trail) without failing the test suite.

### Q5: How do the automated tests maintain independence and prevent test data pollution?
**Answer:** Each test creates unique expense requests using a timestamped prefix (`uniqueTitle("UC5-...")`) and separate test items via API before driving the browser. This guarantees that each test operates on fresh, un-mutated data without relying on the state of previous tests.
