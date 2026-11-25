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
- **HTTP-unreachable branch — verbatim source and test** (`EMPTY_REQUEST`):

  Source: `ExpenseService.java` lines 135–137
  (file: [`src/main/java/com/sandy/expense/service/ExpenseService.java`](file:///c:/Users/Z%20Book/expense-approval/src/main/java/com/sandy/expense/service/ExpenseService.java#L135-L137))
  ```java
  if (r.getItems().isEmpty()) {
      throw ApiException.badRequest("EMPTY_REQUEST", "Add at least one line item before submitting");
  }
  ```
  This guard lives inside `submit(AppUserPrincipal me, Long id)` at lines 127–141 of `ExpenseService.java`.

  Through the HTTP REST layer the matching DTO has `@NotEmpty` on `items` (declared in `ExpenseDtos.CreateRequest`), so Bean Validation rejects the request at the web layer with HTTP 400 before the method is ever called with an empty list. The service-level guard is therefore unreachable via HTTP but is reachable when `ExpenseService` is exercised directly (e.g. a draft request whose items have been cleared programmatically, or future callers that bypass the DTO).

  Team test that covers this branch:
  `tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java` lines 352–364
  (file: [`ExpenseServiceWhiteBoxTest.java`](file:///c:/Users/Z%20Book/expense-approval/tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java#L352-L364))
  ```java
  @Test
  void submit_draftWithNoItems_isRejected_BR1() {
      // Unreachable through the HTTP API (@NotEmpty on CreateRequest.items) but reachable at the
      // service boundary: defensive branch, documented in the equivalent-branch notes.
      ExpenseRequest r = request(33L, alice, eng, RequestStatus.DRAFT);
      when(requests.findById(33L)).thenReturn(Optional.of(r));
      assertThatThrownBy(() -> service.submit(principal(alice), 33L))
              .isInstanceOf(ApiException.class)
              .extracting(e -> ((ApiException) e).getCode())
              .isEqualTo("EMPTY_REQUEST");
      assertThat(r.getStatus()).isEqualTo(RequestStatus.DRAFT);
      assertThat(r.getApprovals()).isEmpty();
  }
  ```

- **BR2 Decision Logic (`assertCanDecide`)** — verbatim source lines 166–180 of `ExpenseService.java`:
  ```java
  private void assertCanDecide(AppUserPrincipal me, ExpenseRequest r) {
      Role needed = r.getStatus().approverRole();
      if (needed == null) {
          throw ApiException.conflict("NOT_PENDING", "This request is not awaiting a decision");
      }
      if (me.getRole() != needed) {
          throw ApiException.forbidden("This stage must be decided by a " + needed);
      }
      if (needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())) {
          throw ApiException.forbidden("You can only decide on requests in your own department");
      }
      if (r.getRequester().getId().equals(me.getUserId())) {
          throw ApiException.forbidden("You cannot decide on your own request");
      }
  }
  ```
  Decision conditions (D1–D4 in the test suite tags):
  - **D1** `needed == null`: terminal states (DRAFT, FINANCE_APPROVED, REJECTED) await nobody.
  - **D2** `me.getRole() != needed`: role mismatch; employee cannot decide on SUBMITTED.
  - **D3** `needed == Role.MANAGER && !dept.equals(myDept)`: compound — both conditions independent for MC/DC.
  - **D4** `requester.getId().equals(me.getUserId())`: self-decision forbidden regardless of role.

---

### 3. Viva Failure Prediction Guide
- **What breaks if someone removes the Manager department check in `assertCanDecide`?**
  - Tests `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441) and `reject_managerOtherDepartment_isForbidden` (line 533) fail — `FORBIDDEN` expected, would pass through without the check.
  - In mutation testing (Task 6), this will kill the mutation replacing the department equality check.
- **What breaks if someone allows a user to approve their own request?**
  - Tests `approve_managerOnOwnRequest_isForbidden_D4_true` (line 479) and `approve_financeOnOwnRequest_isForbidden_D4_true` (line 490) fail.
- **What breaks if someone adds a new state to `RequestStatus`?**
  - Tests `transitionTable`, `enumsExposeExpectedConstants` (which asserts `hasSize(5)`), and `approverRoleIsNullExactlyWhenOnApproveIsNull` all fail — the `@CsvSource` and enum size assertion become stale immediately.
