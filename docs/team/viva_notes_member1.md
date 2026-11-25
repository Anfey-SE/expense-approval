# Viva Readiness Notes — Member 1 (24i-3112)

These notes explain in plain English what the test suite and build wiring do, why each assertion exists, and how to predict what breaks when business rules or transitions change.

---

## Task 2: Build Wiring, JaCoCo Enforcements, and White-Box Test Architecture

### 1. Build & Test Architecture
- **Test Separation**: Per project rules, our tests are kept strictly under `tests/team/unit/` while upstream tests remain under `src/test/java/`. The `build-helper-maven-plugin` adds `tests/team/unit` as a secondary test source root during the `generate-test-sources` phase.
- **JaCoCo Agent & Docker 29 Compatibility**: `jacoco-maven-plugin:prepare-agent` dynamically sets the `@{argLine}` property passed to Surefire. We configured `maven-surefire-plugin` with `<argLine>@{argLine} -Dapi.version=1.44</argLine>` so that JaCoCo instrumentation works seamlessly alongside the Testcontainers Docker 29 API version requirement without collision.
- **Coverage Gate**: The `check` goal enforces a strict 100% line and branch threshold on four core classes:
  1. `com.sandy.expense.service.ExpenseService`
  2. `com.sandy.expense.service.AuthService`
  3. `com.sandy.expense.domain.RequestStatus`
  4. `com.sandy.expense.domain.ExpenseRequest`

---

### 2. Why Every Core Assertion Exists

#### A. Domain State Machine (`RequestStatus` & `ExpenseRequest`)
- `transitionTable(from, approver, next)`:
  - Asserts the exact 5-state transition mapping:
    - `DRAFT`: No approver (`null`), no next approve state (`null`).
    - `SUBMITTED`: Approver role must be `MANAGER`, transitions to `MANAGER_APPROVED`.
    - `MANAGER_APPROVED`: Approver role must be `FINANCE`, transitions to `FINANCE_APPROVED`.
    - `FINANCE_APPROVED` & `REJECTED`: Terminal states with `null` approver and `null` approve state.
  - **Predicting Rule Changes**: If a requirement adds a new role (e.g. `DIRECTOR`) or modifies the transition sequence (e.g. Finance directly approving `SUBMITTED`), this parameterized test immediately fails on the mismatched row.
- `approverRoleIsNullExactlyWhenOnApproveIsNull`:
  - Verifies the state machine invariant: a status can be approved if and only if it defines an approver role.
- `recomputeTotal_noItems_isZeroWithScaleTwo` & `recomputeTotal_sumsItems_atScaleTwo`:
  - Verifies that currency arithmetic uses exact scale (2 decimals) and defaults to `0.00` rather than null or unscaled zero.

#### B. Authentication Service (`AuthService`)
- `register_emailAlreadyTaken_isConflict_andNothingSaved`:
  - Enforces unique email check before password encoding or entity persistence.
- `register_withKnownDepartment_attachesIt` vs `register_withUnknownDepartment_isBadRequest_andNothingSaved`:
  - Proves that foreign keys to departments are validated and unpersisted if invalid (`BAD_DEPARTMENT`).
- `login_badCredentials_is401_andNoTokenIssued`:
  - Asserts authentication failure returns HTTP 401 with code `BAD_CREDENTIALS` and ensures no JWT token is generated.

#### C. Expense Service (`ExpenseService`)
- **HTTP Unreachable Branch Justification (`EMPTY_REQUEST`)**:
  - In `ExpenseService.submit(id, user)`:
    ```java
    if (req.getItems().isEmpty()) {
        throw new ApiException(HttpStatus.BAD_REQUEST, "EMPTY_REQUEST", "Cannot submit request without items");
    }
    ```
  - Through the HTTP REST layer, `@NotEmpty` on the DTO `CreateRequest.items` triggers Bean Validation (400 Bad Request) at the Web layer, so an HTTP request with empty items never reaches `ExpenseService.submit()`.
  - However, in modular architecture or service-level unit testing, a draft request might be manipulated directly. `ExpenseServiceWhiteBoxTest.submit_emptyItems_throwsEmptyRequest` explicitly asserts this service guard, ensuring 100% branch and line coverage for the method.
- **BR2 Decision Logic (`assertCanDecide`)**:
  - Decision condition requires:
    1. Caller role must match `status.approverRole()`.
    2. Caller must not be the submitter (`!request.getUser().getId().equals(decider.getId())`).
    3. If decider is `MANAGER`, decider department must match request department (`decider.getDepartment().getId().equals(request.getDepartment().getId())`).
  - Tested with dedicated white-box tests covering every permutation of matching and non-matching departments, roles, self-approvals, and terminal stages.

---

### 3. Viva Failure Prediction Guide
- **What breaks if someone removes the Manager department check in `assertCanDecide`?**
  - Test `decide_managerDifferentDepartment_isForbidden` fails immediately (`FORBIDDEN` expected, but would pass if check was dropped).
  - In mutation testing (Task 6), this will kill the mutation replacing the department check.
- **What breaks if someone allows an Employee to approve their own request?**
  - Test `decide_selfDecision_isForbidden` fails.
- **What breaks if someone adds a new state to `RequestStatus`?**
  - Tests `transitionTable`, `enumsExposeExpectedConstants` (size check), and `approverRoleIsNullExactlyWhenOnApproveIsNull` fail.
