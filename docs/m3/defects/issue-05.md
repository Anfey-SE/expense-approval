# Issue #05: Usability Defect — Blank Rejection Reason Accepted Without Actionable Employee Guidance

- **Title:** Rejection Endpoint and UI Allow Omission of Feedback Reason on Rejected Expenses
- **Category:** Usability & Domain Workflow
- **Severity:** Medium
- **Priority:** Medium (P2)
- **Status:** Open (Corroborated with Member 2 Finding EW-2)
- **Triage Decision:** Scheduled for business logic enhancement; add `@NotBlank` validation on `DecisionRequest.comment`.
- **Linked Risk Register ID:** **PR-04** (*Blank rejection comment accepted*, Score: 12)
- **Evidence Link:** [`docs/m3/use-cases.md`](../use-cases.md#uc6) and [`tests/team/e2e/tests/uc5-uc6-finance.spec.ts`](../../tests/team/e2e/tests/uc5-uc6-finance.spec.ts#L173-L200)

---

## Description & User Impact
In Use Case 6 (Finance Rejection) and Use Case 4 (Manager Rejection), approvers are permitted to reject an employee's expense claim with an entirely blank or whitespace comment. When an employee reviews the rejected claim in their history, the rejection trail displays `—` without explaining why the reimbursement was refused, forcing manual out-of-band email inquiries.

## Steps to Reproduce
1. Log in as Finance approver (`fiona@acme.com`).
2. Open a `MANAGER_APPROVED` request.
3. Leave the `Comment (optional)` field completely blank.
4. Click `Reject`.
5. Observe that the request successfully transitions to `REJECTED` and an approval trail row is created with `comment: ""`.

## Expected vs Actual
- **Expected:** Business rule should enforce a mandatory explanation (`@NotBlank(message = "Rejection reason is required")`) when rejecting, providing actionable feedback to the requester.
- **Actual:** Backend accepts blank comments unconditionally (`comment == null ? "" : comment`), leaving employees uninformed.

## Recommended Fix
In `com.sandy.expense.service.ExpenseService.java`:
```java
if (action == ApprovalAction.REJECT && (comment == null || comment.isBlank())) {
    throw ApiException.badRequest("COMMENT_REQUIRED", "A comment is required when rejecting an expense request");
}
```
