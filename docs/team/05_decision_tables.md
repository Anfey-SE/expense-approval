# Task A — Decision Tables

This document lists **every condition combination** for each business rule with two or more conditions, maps each row to the test method in `ExpenseServiceWhiteBoxTest` that covers it, and marks rows that are impossible or short-circuited.

---

## 1. `assertCanDecide` (BR2 / BR4) — `ExpenseService.java` lines 166–180

```java
// ExpenseService.java lines 166-180
private void assertCanDecide(AppUserPrincipal me, ExpenseRequest r) {
    Role needed = r.getStatus().approverRole();
    if (needed == null) {                                                       // C1
        throw ApiException.conflict("NOT_PENDING", "This request is not awaiting a decision");
    }
    if (me.getRole() != needed) {                                               // C2
        throw ApiException.forbidden("This stage must be decided by a " + needed);
    }
    if (needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())) { // C3 = A && B
        throw ApiException.forbidden("You can only decide on requests in your own department");
    }
    if (r.getRequester().getId().equals(me.getUserId())) {                       // C4
        throw ApiException.forbidden("You cannot decide on your own request");
    }
}
```

### Conditions

| ID | Condition | True when | False when |
|----|-----------|-----------|------------|
| C1 | Status awaits a decision | `approverRole() != null` (SUBMITTED or MANAGER_APPROVED) | DRAFT, FINANCE_APPROVED, REJECTED (`approverRole()` returns `null`) |
| C2 | Caller's role owns the stage | `me.getRole() == needed` | Role mismatch |
| C3 | For MANAGER: same department | Compound `A && B`: **A** = `needed == MANAGER`, **B** = dept mismatch. The whole guard is `true` (throws) when both A and B are true. For FINANCE stage, A is `false` so the `&&` short-circuits and B is never evaluated. |
| C4 | Caller is the requester | `r.getRequester().getId().equals(me.getUserId())` |

### Full decision table (all 16 theoretical C1 x C2 x C3 x C4 combinations)

Because the checks are sequential `if` guards, **earlier failures short-circuit later conditions**: C2 is never evaluated when C1 throws, C3 is never evaluated when C2 throws, and C4 is never evaluated when C3 throws.

| Row | C1 awaits? | C2 role match? | C3 mgr+wrong dept? | C4 is self? | Reachable? | Outcome | Test method(s) |
|-----|------------|----------------|---------------------|-------------|------------|---------|----------------|
| 1 | F | F | F | F | Short-circuit at C1 | `NOT_PENDING` (409) | `approve_statusAwaitingNobody_isNotPending_D1` (DRAFT, FINANCE_APPROVED, REJECTED) |
| 2 | F | F | F | T | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 3 | F | F | T | F | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 4 | F | F | T | T | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 5 | F | T | F | F | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 6 | F | T | F | T | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 7 | F | T | T | F | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 8 | F | T | T | T | Short-circuit at C1 | `NOT_PENDING` (409) | (same as row 1) |
| 9 | T | F | F | F | Short-circuit at C2 | Forbidden: wrong role (403) | `approve_employeeOnSubmitted_wrongRole_D2`, `approve_managerOnManagerApproved_wrongRole_D2` |
| 10 | T | F | F | T | Short-circuit at C2 | Forbidden: wrong role (403) | (same as row 9) |
| 11 | T | F | T | F | Short-circuit at C2 | Forbidden: wrong role (403) | (same as row 9) |
| 12 | T | F | T | T | Short-circuit at C2 | Forbidden: wrong role (403) | (same as row 9) |
| 13 | T | T | T (MGR, wrong dept) | F | Short-circuit at C3 | Forbidden: wrong department (403) | `approve_managerOtherDepartment_isForbidden_D3_BtoTrue`, `approve_managerPrincipalWithoutDepartment_isForbidden` |
| 14 | T | T | T (MGR, wrong dept) | T | Short-circuit at C3 | Forbidden: wrong department (403) | (same as row 13) |
| 15 | T | T | F | T (is self) | **Reachable** | Forbidden: self-decision (403) | `approve_managerOnOwnRequest_isForbidden_D4_true` (MGR stage), `approve_financeOnOwnRequest_isForbidden_D4_true` (FIN stage) |
| 16 | T | T | F | F (not self) | **Reachable** | **ALLOWED** | `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (MGR stage), `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (FIN stage) |

### Collapsed reachable-path table (7 paths)

| Path | Stage | C1 | C2 | C3 dept OK? | C4 not self? | Outcome | Test method |
|------|-------|----|----|-------------|--------------|---------|-------------|
| P1 | DRAFT / FIN_APP / REJECTED | F | -- | -- | -- | `NOT_PENDING` (409) | `approve_statusAwaitingNobody_isNotPending_D1`, `reject_statusAwaitingNobody_isNotPending_D1` |
| P2 | SUBMITTED | T | F | -- | -- | Forbidden: wrong role | `approve_employeeOnSubmitted_wrongRole_D2` |
| P3 | MANAGER_APPROVED | T | F | -- | -- | Forbidden: wrong role | `approve_managerOnManagerApproved_wrongRole_D2` |
| P4 | SUBMITTED (MGR) | T | T | F (wrong dept) | -- | Forbidden: wrong dept | `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` |
| P5 | SUBMITTED (MGR) | T | T | T (same dept) | F (is self) | Forbidden: self-decision | `approve_managerOnOwnRequest_isForbidden_D4_true` |
| P6 | SUBMITTED (MGR) | T | T | T (same dept) | T | **ALLOWED -> MANAGER_APPROVED** | `approve_managerSameDepartment_isAllowed_D3_BtoFalse` |
| P7 | MGR_APPROVED (FIN) | T | T | n/a (A=false) | F (is self) | Forbidden: self-decision | `approve_financeOnOwnRequest_isForbidden_D4_true` |
| P8 | MGR_APPROVED (FIN) | T | T | n/a (A=false) | T | **ALLOWED -> FINANCE_APPROVED** | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |

### Why some combinations are impossible

1. **No EMPLOYEE approver**: `RequestStatus.approverRole()` returns `MANAGER` or `FINANCE`; it never returns `EMPLOYEE`. An employee caller with C1=T always fails at C2.
2. **C3 is irrelevant at the FINANCE stage**: condition A (`needed == Role.MANAGER`) is `false`, so Java's `&&` short-circuit skips B (the department comparison). Department mismatch is **never checked** for the FINANCE stage.
3. **Short-circuit ordering**: the `if` chain at lines 168, 171, 174, 177 means later conditions are only evaluated when all earlier ones pass.

> [!NOTE]
> The same `assertCanDecide` method is called by both `approve()` (line 146) and `reject()` (line 155). The reject-path tests mirror the approve paths: `reject_managerOnSubmitted_setsRejected_withReason`, `reject_financeOnManagerApproved_setsRejected`, `reject_managerOtherDepartment_isForbidden`, `reject_statusAwaitingNobody_isNotPending_D1`, `reject_twice_secondAttemptIsNotPending_andTrailHasExactlyOneRow`.

---

## 2. `submit` (BR1 / BR3) — `ExpenseService.java` lines 127–141

```java
// ExpenseService.java lines 127-141
@Transactional
public RequestDetail submit(AppUserPrincipal me, Long id) {
    ExpenseRequest r = load(id);
    if (!r.getRequester().getId().equals(me.getUserId())) {       // C1: owner check
        throw ApiException.forbidden("You can only submit your own requests");
    }
    if (r.getStatus() != RequestStatus.DRAFT) {                   // C2: status check
        throw ApiException.conflict("NOT_SUBMITTABLE", "Only DRAFT requests can be submitted");
    }
    if (r.getItems().isEmpty()) {                                  // C3: items check
        throw ApiException.badRequest("EMPTY_REQUEST", "Add at least one line item before submitting");
    }
    transition(r, me, ApprovalAction.SUBMIT, RequestStatus.SUBMITTED, "");
    r.setSubmittedAt(Instant.now());
    return RequestDetail.of(r);
}
```

### Conditions

| ID | Condition | True when | False when |
|----|-----------|-----------|------------|
| C1 | Caller is the owner | `requester.id == me.userId` | Different user |
| C2 | Status is DRAFT | `r.getStatus() == RequestStatus.DRAFT` | Any other status |
| C3 | At least one line item | `!r.getItems().isEmpty()` | Empty items list |

### Full decision table (8 combinations)

| Row | C1 owner? | C2 DRAFT? | C3 has items? | Reachable? | Outcome | Test method |
|-----|-----------|-----------|---------------|------------|---------|-------------|
| 1 | F | F | F | Short-circuit at C1 | Forbidden (403) | `submit_notOwner_isForbidden` |
| 2 | F | F | T | Short-circuit at C1 | Forbidden (403) | (same as row 1) |
| 3 | F | T | F | Short-circuit at C1 | Forbidden (403) | (same as row 1) |
| 4 | F | T | T | Short-circuit at C1 | Forbidden (403) | (same as row 1) |
| 5 | T | F | F | Short-circuit at C2 | `NOT_SUBMITTABLE` (409) | `submit_anyNonDraftStatus_isConflict` (parameterised: SUBMITTED, MANAGER_APPROVED, FINANCE_APPROVED, REJECTED) |
| 6 | T | F | T | Short-circuit at C2 | `NOT_SUBMITTABLE` (409) | (same as row 5) |
| 7 | T | T | F | **Reachable** | `EMPTY_REQUEST` (400) | `submit_draftWithNoItems_isRejected_BR1` |
| 8 | T | T | T | **Reachable** | **SUCCESS -> SUBMITTED** | `submit_success_movesToSubmitted_writesOneSubmitTrailRow` |

> [!NOTE]
> Row 7 (`EMPTY_REQUEST`) is unreachable through the HTTP API because `@NotEmpty` on `CreateRequest.items` rejects an empty list before the controller dispatches. The service guard is defensive; see the equivalent-branch notes in [04_mutation_testing.md](04_mutation_testing.md).

---

## 3. `update` — `ExpenseService.java` lines 103–122

```java
// ExpenseService.java lines 103-122
@Transactional
public RequestDetail update(AppUserPrincipal me, Long id, CreateRequest input) {
    ExpenseRequest r = load(id);
    if (!r.getRequester().getId().equals(me.getUserId())) {       // C1: owner check
        throw ApiException.forbidden("You can only edit your own requests");
    }
    if (r.getStatus() != RequestStatus.DRAFT) {                   // C2: status check
        throw ApiException.conflict("NOT_EDITABLE", "Only DRAFT requests can be edited");
    }
    r.setTitle(input.title());
    r.setDescription(input.description() == null ? "" : input.description());
    if (input.currency() != null && !input.currency().isBlank()) {
        r.setCurrency(input.currency().toUpperCase());
    }
    r.getItems().clear();
    for (ItemInput it : input.items()) {
        r.addItem(toItem(it));
    }
    r.recomputeTotal();
    return RequestDetail.of(r);
}
```

### Conditions

| ID | Condition | True when | False when |
|----|-----------|-----------|------------|
| C1 | Caller is the owner | `requester.id == me.userId` | Different user |
| C2 | Status is DRAFT | `r.getStatus() == RequestStatus.DRAFT` | Any other status |

### Full decision table (4 combinations)

| Row | C1 owner? | C2 DRAFT? | Reachable? | Outcome | Test method |
|-----|-----------|-----------|------------|---------|-------------|
| 1 | F | F | Short-circuit at C1 | Forbidden (403) | `update_notOwner_isForbidden` |
| 2 | F | T | Short-circuit at C1 | Forbidden (403) | (same as row 1) |
| 3 | T | F | **Reachable** | `NOT_EDITABLE` (409) | `update_requestNotDraft_isConflict_andRequestUnchanged` |
| 4 | T | T | **Reachable** | **SUCCESS (stays DRAFT)** | `update_nullCurrency_keepsExistingCurrency_andClearsDescription`, `update_blankCurrency_keepsExistingCurrency`, `update_newCurrency_isUppercased` |

> [!NOTE]
> `update` has no `items.isEmpty()` guard. The DTO's `@NotEmpty` on `CreateRequest.items` enforces the minimum at the web layer.

---

## 4. Coverage summary

**All decision-table rows are covered by existing tests.** No new tests were needed for Task A.

| Business rule | Conditions | Theoretical rows | Reachable paths | Tests covering them |
|---------------|------------|-------------------|-----------------|---------------------|
| `assertCanDecide` (BR2/BR4) | 4 (C1-C4) | 16 | 8 (7 unique outcomes) | 13 test methods (approve + reject variants) |
| `submit` (BR1/BR3) | 3 (C1-C3) | 8 | 4 | 4 test methods (incl. parameterised x4 statuses) |
| `update` | 2 (C1-C2) | 4 | 3 | 4 test methods |
