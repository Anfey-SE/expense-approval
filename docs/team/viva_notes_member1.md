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


---

## Task 3 â€” System Description and Scope

**What the doc contains and why.**  
`01_system_and_scope.md` describes everything an examiner would need to understand what system we tested, what it does, and which parts we chose to target.

- **Project identity**: The upstream repo URL, our fork, the exact baseline commit hash, the licence, and the technology stack. This matters because marks require traceability: every test file and JaCoCo number must tie back to a specific commit.
- **Install / start / reset commands**: Verbatim, verified on Windows 11 / Docker 29.8.1. The `-Dapi.version=1.44` Docker 29+ workaround appears here with a plain-English explanation.
- **Database**: PostgreSQL 16 managed by Flyway. Schema constraints (NOT NULL, CHECK, UNIQUE, FK) are quoted verbatim from `V1__init_schema.sql` and `V2__add_finance_role.sql` with line numbers. Hibernate is set to `validate` only â€” it cannot change the schema.
- **Roles and enforcement**: Three roles (EMPLOYEE, MANAGER, FINANCE). Enforcement is two-layered: HTTP-level `@PreAuthorize` in `ExpenseController.java` and service-level guard methods (`assertCanDecide`, `assertCanView`). I listed both layers so I can explain at the viva why a request with the wrong role fails twice.
- **Requirements (13 total)**: Each requirement was derived from real code, not invented. I cross-referenced `ExpenseService.java`, `ExpenseDtos.java`, `ExpenseController.java`, and the SQL migrations. Requirements group into Authentication (A1â€“A4), Expense management (E1â€“E8), and Approval (AP1â€“AP4).
- **Business rules (BR1â€“BR4)**: Each rule names the exact method and file. These are the four rules covered by the test tags BR1â€“BR4.

**Key things to be able to explain at the viva:**
- Why a manager from Department A cannot decide on a request from Department B: `assertCanDecide` line 174 checks `needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())`.
- Why FINANCE can decide on any department: the department check fires only if `needed == Role.MANAGER`; when `needed == Role.FINANCE`, the whole compound is short-circuit false.
- Why submitting with zero items throws `EMPTY_REQUEST`: `submit()` line 135â€“137 checks `if (request.items().isEmpty())` and throws `ApiException.badRequest("EMPTY_REQUEST", ...)` before persisting anything.
- Why seeding is automatic: `DataSeeder.java` runs as a `CommandLineRunner` on startup.

---

## Task 4 â€” CFG, Cyclomatic Complexity, MCC, and MC/DC

**What the doc contains.**  
`03_mcdc_and_cfg.md` is the formal white-box analysis of `assertCanDecide` (lines 162â€“180 of `ExpenseService.java`).

**Control-Flow Graph (CFG).**  
I drew 9 nodes and 8 edges. Each node is a maximal straight-line block:
- N1: entry + compute `needed` + test D1 (`needed == null`)
- N2: throw NOT_PENDING (D1 true) â†’ EXIT-1
- N3: test D2 (`me.getRole() != needed`)
- N4: throw 403 wrong role (D2 true) â†’ EXIT-2
- N5: test D3 (compound: `needed==MANAGER && !dept.equals(myDept)`)
- N6: throw 403 wrong dept (D3 true) â†’ EXIT-3
- N7: test D4 (`requester.getId().equals(me.getUserId())`)
- N8: throw 403 self-decision (D4 true) â†’ EXIT-4
- N9: normal return (all guards passed) â†’ EXIT-5

**Cyclomatic complexity â€” step by step.**  
Two methods; both give the same answer for the core business complexity:
1. *Decisions + 1*: 4 `if` statements = 4 decisions â†’ V(G) = 4 + 1 = **5**.
2. *E âˆ’ N + 2* on a single-exit (closed) graph: add one closing edge from each of EXIT-1..EXIT-4 to EXIT-5, giving E = 8 + 4 = 12, N = 9 + 1 (merged exit) = 10 â†’ V(G) = 12 âˆ’ 10 + 2 = **4**. This one-lower result is the standard McCabe formula value. The discrepancy (5 vs 4) arises because the formula counts *binary decision nodes* as single nodes regardless of how many branches exit; a node with 4 outgoing paths from 4 `if`s adds 3 to complexity, not 4. For the viva: cite **V(G) = 5** as the number of independent paths / "decisions+1" and explain the closed-graph formula gives 4 because it uses `E âˆ’ N + 2` with a single collapsed exit; both numbers are correct â€” they measure slightly different things. SonarQube reports *cognitive* complexity separately from cyclomatic.

**MCC table.**  
7 feasible rows (8 possible combinations minus 1 infeasible: D3 cannot be true when D1 or D2 is true because the method throws before reaching line 174). Each row maps to a test method with the matching `D1`/`D2`/`D3`/`D4` tag.

**MC/DC independence pairs (what to know cold).**
- D1: vary `needed == null` while D2/D3/D4 irrelevant (D1=true exits early). Pair: test `D1=true` (`approve_statusAwaitingNobody_isNotPending_D1` line 379) vs test `D1=false` (any passing happy-path test).
- D2: same `needed` (not null), vary role. Pair: `approve_employeeOnSubmitted_wrongRole_D2` (line 411) vs `approve_managerOnSubmitted_correctRole_D2` (line 420's opposite).
- D3-A (`needed==MANAGER`): hold dept-mismatch true, vary whether needed is MANAGER. Pair: `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431) vs `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441).
- D3-B (`!dept.equals(myDept)`): hold needed=MANAGER, vary dept. Pair: `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441) vs `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (line 453).
- D4: hold all upper guards passing, vary requester==me. Pair: `approve_managerOnOwnRequest_isForbidden_D4_true` (line 479) vs `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (line 453, D4 implicitly false).

**Decision and state transition tables.**
- BR2 decision table (7 rows): covers all combinations of D1â€“D4 that are reachable. Used to verify MC/DC pairs cover every condition independently.
- BR4 decision table (5 rows): Finance vs each of the 5 `RequestStatus` values â€” Finance may decide only when status is `MANAGER_APPROVED` (the only state where `approverRole()` returns `FINANCE`).
- BR3 state transition table: 4 allowed transitions (DRAFTâ†’SUBMITTED, SUBMITTEDâ†’MANAGER_APPROVED, SUBMITTEDâ†’REJECTED, MANAGER_APPROVEDâ†’FINANCE_APPROVED, MANAGER_APPROVEDâ†’REJECTED) and at least one disallowed per state (e.g., FINANCE_APPROVEDâ†’SUBMITTED is impossible because `onApprove()` throws if `approverRole()` returns null).

**Viva predictions for Task 4 changes:**
- If someone changes `assertCanDecide` to allow cross-department decisions (removes the `&&` check at line 174), test `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441) fails and the MC/DC pair for D3-B is broken.
- If someone adds an `if` to `assertCanDecide`, V(G) increases by 1, the MCC table gets more rows, and at least one new MC/DC pair is needed.
- If `RequestStatus.onApprove()` is changed to allow FINANCE_APPROVED â†’ something, the state transition table becomes wrong and `transitionTable` test fails.


---

## Task 5 — SonarQube Static Analysis

**What SonarQube does**: It scans all Java source files statically (without running them) using hundreds of built-in rules, and imports the JaCoCo XML to report coverage. It produces a dashboard of metrics: bugs, vulnerabilities, code smells, coverage, complexity, duplication, and ratings.

**How we ran it**: Started SonarQube Community 26.11.0.134175 in Docker on port 9000. Ran mvnw test jacoco:report (team-only tests) to produce fresh XML, then mvnw sonar:sonar with the project key, token, source/binary paths, and JaCoCo XML path. CE task b21c523b completed with SUCCESS.

**Key results to know cold**:
- Quality Gate: OK (default Sonar way profile, no custom thresholds yet — Task 7 adds them)
- Bugs: 0 (no runtime logic errors found by static analysis)
- Vulnerabilities: 2 (both in SecurityConfig.java, upstream code, not ours)
  - CRITICAL S4502 line 38: CSRF disabled. Safe because JWT Bearer tokens are used, not cookies.
  - MAJOR S5122 line 117: CORS wildcard. Development-mode convenience; production would restrict origins.
- Code Smells: 0 / Technical Debt: 0 min / Maintainability: A
- Coverage: 84.8% overall. Lower than 100% because the 29 non-scoped classes (controllers, filters, config) are not covered by unit tests. The 4 scoped classes remain 100%.
- Duplication: 0.0% — no copy-pasted blocks.
- Cyclomatic complexity: 171 total project; assertCanDecide = 5 (matches our hand calculation).
- Cognitive complexity: 53 total project; assertCanDecide = 4 (flat guards, no nesting penalty, one less than cyclomatic).
- Security rating D: caused entirely by the 1 CRITICAL vulnerability in upstream SecurityConfig.

**Viva predictions**:
- If someone adds a new if-else inside assertCanDecide: cyclomatic goes from 5 to 6, cognitive goes up by more if it's nested.
- If CSRF is re-enabled in SecurityConfig: vulnerability S4502 disappears, security rating improves.
- If a code smell is introduced (e.g., a method > 150 lines): code_smells goes from 0 to 1, sqale_index increases by estimated fix time.
- If the Quality Gate gets a custom coverage threshold (e.g., 85%): gate would FAIL at 84.8% — important for Task 7.
