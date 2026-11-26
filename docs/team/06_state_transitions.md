# Task B — State Transition Table

## 1. States and events

### States (`RequestStatus.java` lines 13–18)

| State | `approverRole()` | `onApprove()` |
|-------|-------------------|---------------|
| `DRAFT` | `null` | `null` |
| `SUBMITTED` | `MANAGER` | `MANAGER_APPROVED` |
| `MANAGER_APPROVED` | `FINANCE` | `FINANCE_APPROVED` |
| `FINANCE_APPROVED` | `null` | `null` |
| `REJECTED` | `null` | `null` |

```java
// RequestStatus.java lines 13-37
public enum RequestStatus {
    DRAFT,
    SUBMITTED,
    MANAGER_APPROVED,
    FINANCE_APPROVED,
    REJECTED;

    public Role approverRole() {
        return switch (this) {
            case SUBMITTED -> Role.MANAGER;
            case MANAGER_APPROVED -> Role.FINANCE;
            default -> null;
        };
    }

    public RequestStatus onApprove() {
        return switch (this) {
            case SUBMITTED -> MANAGER_APPROVED;
            case MANAGER_APPROVED -> FINANCE_APPROVED;
            default -> null;
        };
    }
}
```

### Events

| Event | Service method | Who may trigger |
|-------|---------------|-----------------|
| **create** | `create()` | Any employee (new request starts at DRAFT) |
| **update** | `update()` | Owner only |
| **submit** | `submit()` | Owner only |
| **approve** | `approve()` | Stage owner (MANAGER or FINANCE) who is not the requester |
| **reject** | `reject()` | Stage owner (MANAGER or FINANCE) who is not the requester |

---

## 2. Full state transition table

Legend: check = allowed transition, cross = disallowed (error code shown).

| Current state | create / update | submit | approve (stage owner) | reject (stage owner) |
|---------------|-----------------|--------|-----------------------|----------------------|
| *(no state)* | -> **DRAFT** | -- | -- | -- |
| **DRAFT** | -> DRAFT (update) | -> **SUBMITTED** (if has items) | ✗ `NOT_PENDING` | ✗ `NOT_PENDING` |
| **SUBMITTED** | ✗ `NOT_EDITABLE` | ✗ `NOT_SUBMITTABLE` | -> **MANAGER_APPROVED** (by MGR) | -> **REJECTED** (by MGR) |
| **MANAGER_APPROVED** | ✗ `NOT_EDITABLE` | ✗ `NOT_SUBMITTABLE` | -> **FINANCE_APPROVED** (by FIN) | -> **REJECTED** (by FIN) |
| **FINANCE_APPROVED** | ✗ `NOT_EDITABLE` | ✗ `NOT_SUBMITTABLE` | ✗ `NOT_PENDING` | ✗ `NOT_PENDING` |
| **REJECTED** | ✗ `NOT_EDITABLE` | ✗ `NOT_SUBMITTABLE` | ✗ `NOT_PENDING` | ✗ `NOT_PENDING` |

---

## 3. Test coverage per cell

### Allowed transitions (all tested)

| Transition | Test method |
|------------|-------------|
| (new) -> DRAFT | `create_nullCurrencyAndDescription_defaultsToUsdAndEmpty`, `create_lowercaseCurrency_isUppercased_andDescriptionKept`, `create_amountIsRoundedHalfUpToTwoDecimals_andTotalIsSum`, `create_copiesTitleAndAllItemFields` |
| DRAFT -> DRAFT (update) | `update_nullCurrency_keepsExistingCurrency_andClearsDescription`, `update_blankCurrency_keepsExistingCurrency`, `update_newCurrency_isUppercased` |
| DRAFT -> SUBMITTED | `submit_success_movesToSubmitted_writesOneSubmitTrailRow` |
| SUBMITTED -> MANAGER_APPROVED | `approve_managerSameDepartment_isAllowed_D3_BtoFalse` |
| SUBMITTED -> REJECTED | `reject_managerOnSubmitted_setsRejected_withReason` |
| MANAGER_APPROVED -> FINANCE_APPROVED | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |
| MANAGER_APPROVED -> REJECTED | `reject_financeOnManagerApproved_setsRejected` |

### Full happy path

`fullHappyPath_draftToFinanceApproved_hasThreeTrailRowsInOrder` exercises DRAFT -> SUBMITTED -> MANAGER_APPROVED -> FINANCE_APPROVED in one test with three service calls and verifies the three approval-trail records in order.

### Disallowed transitions (at least one per state)

| State | Disallowed event | Error code | Test method |
|-------|------------------|------------|-------------|
| **DRAFT** | approve | `NOT_PENDING` | `approve_statusAwaitingNobody_isNotPending_D1` (parameterised, includes DRAFT) |
| **DRAFT** | reject | `NOT_PENDING` | `reject_statusAwaitingNobody_isNotPending_D1` (parameterised, includes DRAFT) |
| **SUBMITTED** | update | `NOT_EDITABLE` | `update_requestNotDraft_isConflict_andRequestUnchanged` |
| **SUBMITTED** | submit | `NOT_SUBMITTABLE` | `submit_anyNonDraftStatus_isConflict` (parameterised, includes SUBMITTED) |
| **MANAGER_APPROVED** | submit | `NOT_SUBMITTABLE` | `submit_anyNonDraftStatus_isConflict` (parameterised, includes MANAGER_APPROVED) |
| **FINANCE_APPROVED** | approve | `NOT_PENDING` | `approve_statusAwaitingNobody_isNotPending_D1` (parameterised, includes FINANCE_APPROVED) |
| **FINANCE_APPROVED** | submit | `NOT_SUBMITTABLE` | `submit_anyNonDraftStatus_isConflict` (parameterised, includes FINANCE_APPROVED) |
| **REJECTED** | reject | `NOT_PENDING` | `reject_statusAwaitingNobody_isNotPending_D1` (parameterised, includes REJECTED) |
| **REJECTED** | submit | `NOT_SUBMITTABLE` | `submit_anyNonDraftStatus_isConflict` (parameterised, includes REJECTED) |

### Additional re-entry guard

| Scenario | Test method |
|----------|-------------|
| reject then reject again (REJECTED -> reject) | `reject_twice_secondAttemptIsNotPending_andTrailHasExactlyOneRow` |

---

## 4. State diagram

```
         create
           |
           v
        +-------+
        | DRAFT |<------- update (owner, stays DRAFT)
        +-------+
           |
           | submit (owner, has items)
           v
      +-----------+
      | SUBMITTED |
      +-----------+
        |       |
approve |       | reject
(MGR)   |       | (MGR)
        v       v
 +------------------+     +----------+
 | MANAGER_APPROVED | --> | REJECTED |
 +------------------+     +----------+
        |       |              ^
approve |       | reject       |
(FIN)   |       | (FIN)       /
        v       +------------+
 +------------------+
 | FINANCE_APPROVED |
 +------------------+
```

---

## 5. Gap analysis

**All 7 allowed transitions are tested.** Each of the 5 states has **at least one disallowed event tested**:

| State | Disallowed events tested |
|-------|--------------------------|
| DRAFT | approve (D1), reject (D1) |
| SUBMITTED | update, submit |
| MANAGER_APPROVED | submit |
| FINANCE_APPROVED | approve (D1), submit |
| REJECTED | reject (D1), submit |

**No new tests were needed for Task B.**
