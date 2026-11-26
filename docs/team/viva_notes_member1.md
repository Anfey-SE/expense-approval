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

## Task 3 — System Description and Scope

**What the doc contains and why.**  
`01_system_and_scope.md` describes everything an examiner would need to understand what system we tested, what it does, and which parts we chose to target.

- **Project identity**: The upstream repo URL, our fork, the exact baseline commit hash, the licence, and the technology stack. This matters because marks require traceability: every test file and JaCoCo number must tie back to a specific commit.
- **Install / start / reset commands**: Verbatim, verified on Windows 11 / Docker 29.8.1. The `-Dapi.version=1.44` Docker 29+ workaround appears here with a plain-English explanation.
- **Database**: PostgreSQL 16 managed by Flyway. Schema constraints (NOT NULL, CHECK, UNIQUE, FK) are quoted verbatim from `V1__init_schema.sql` and `V2__add_finance_role.sql` with line numbers. Hibernate is set to `validate` only — it cannot change the schema.
- **Roles and enforcement**: Three roles (`EMPLOYEE`, `MANAGER`, `FINANCE`). Enforcement is two-layered: HTTP-level `@PreAuthorize` in `ExpenseController.java` and service-level guard methods (`assertCanDecide`, `assertCanView`). I listed both layers so I can explain at the viva why a request with the wrong role fails twice.
- **Requirements (13 total)**: Each requirement was derived from real code, not invented. I cross-referenced `ExpenseService.java`, `ExpenseDtos.java`, `ExpenseController.java`, and the SQL migrations. Requirements group into Authentication (A1–A4), Expense management (E1–E8), and Approval (AP1–AP4).
- **Business rules (BR1–BR4)**: Each rule names the exact method and file. These are the four rules covered by the test tags BR1–BR4.

**Key things to be able to explain at the viva:**
- Why a manager from Department A cannot decide on a request from Department B: `assertCanDecide` line 174 checks `needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())`.
- Why `FINANCE` can decide on any department: the department check fires only if `needed == Role.MANAGER`; when `needed == Role.FINANCE`, the whole compound is short-circuit false.
- Why submitting with zero items throws `EMPTY_REQUEST`: `submit()` lines 135–137 check `if (r.getItems().isEmpty())` and throw `ApiException.badRequest("EMPTY_REQUEST", ...)` before persisting anything.
- Why seeding is automatic: `DataSeeder.java` runs as a `CommandLineRunner` on startup.

---

## Task 4 — CFG, Cyclomatic Complexity, MCC, and MC/DC

**What the doc contains.**  
`03_mcdc_and_cfg.md` is the formal white-box analysis of `assertCanDecide` (lines 162–180 of `ExpenseService.java`).

**Control-Flow Graph (CFG).**  
Single-entry, single-exit CFG with short-circuit `&&` expanded into two atomic predicate nodes and all exit paths collapsed into `[EXIT]`: 11 nodes and 15 edges:
- `N1`: entry + compute `needed` + test D1 (`needed == null`)
- `N2`: throw `NOT_PENDING` (D1 true) → `EXIT`
- `N3`: test D2 (`me.getRole() != needed`)
- `N4`: throw 403 wrong role (D2 true) → `EXIT`
- `N5a`: test D3-A (`needed == Role.MANAGER`) — false short-circuits to `N7`
- `N5b`: test D3-B (`!dept.equals(myDept)`)
- `N6`: throw 403 wrong dept (D3-B true) → `EXIT`
- `N7`: test D4 (`requester.getId().equals(me.getUserId())`)
- `N8`: throw 403 self-decision (D4 true) → `EXIT`
- `N9`: normal return (all guards passed) → `EXIT`
- `EXIT`: collapsed terminal exit node

**Cyclomatic complexity — step by step (both methods give 6).**  
1. *E − N + 2* on single-entry, single-exit CFG: E = 15, N = 11 → `V(G) = 15 − 11 + 2 = 6`.
2. *Decisions + 1*: base 1 + 4 `if` statements + 1 `&&` operator (which adds a separate binary branch path) → `V(G) = 1 + 4 + 1 = 6`.
SonarQube does **not** expose per-method complexity (API stops at file level); for `ExpenseService.java` as a whole (14 functions, 181 NCLOC), Sonar reports cyclomatic = 45, cognitive = 22.

**MCC table.**  
7 feasible rows (D3 cannot be reached when D1 or D2 is true because the method throws before reaching line 174). Each row maps to a test method with the matching `D1`/`D2`/`D3`/`D4` tag.

**MC/DC independence pairs (what to know cold).**
- D1: vary `needed == null` while D2/D3/D4 irrelevant (D1=true exits early). Pair: `approve_statusAwaitingNobody_isNotPending_D1` (line 379) vs any passing happy-path test.
- D2: same `needed` (not null), vary role. Pair: `approve_employeeOnSubmitted_wrongRole_D2` (line 411) vs happy-path test.
- D3-A (`needed==MANAGER`): hold dept-mismatch true, vary whether needed is MANAGER. Pair: `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431) vs `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441).
- D3-B (`!dept.equals(myDept)`): hold needed=MANAGER, vary dept. Pair: `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441) vs `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (line 453).
- D4: hold all upper guards passing, vary requester==me. Pair: `approve_managerOnOwnRequest_isForbidden_D4_true` (line 479) vs `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (line 453, D4 implicitly false).

**Decision and state transition tables.**
- BR2 decision table (7 rows): covers all reachable combinations of D1–D4.
- BR4 decision table (5 rows): Finance vs each of the 5 `RequestStatus` values — Finance may decide only when status is `MANAGER_APPROVED` (the only state where `approverRole()` returns `FINANCE`).
- BR3 state transition table: allowed transitions (`DRAFT→SUBMITTED`, `SUBMITTED→MANAGER_APPROVED`, `SUBMITTED→REJECTED`, `MANAGER_APPROVED→FINANCE_APPROVED`, `MANAGER_APPROVED→REJECTED`) and disallowed transitions from every state.

**Viva predictions for Task 4 changes:**
- If someone changes `assertCanDecide` to allow cross-department decisions (removes the `&&` check at line 174), test `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441) fails, the MC/DC pair for D3-B breaks, and hand-computed V(G) drops from 6 to 5.
- If someone adds an `if` to `assertCanDecide`, hand-computed V(G) increases by 1 (from 6 to 7), and at least one new MC/DC pair is needed.
- If `RequestStatus.onApprove()` is changed to allow `FINANCE_APPROVED →` another state, `transitionTable` test fails.

---

## Task 5 — SonarQube Static Analysis

**What SonarQube does**: It scans all Java source files statically (without running them) using built-in rules, and imports `target/site/jacoco/jacoco.xml` to report coverage. It produces a dashboard of metrics: bugs, vulnerabilities, code smells, coverage, complexity, duplication, and ratings.

**How we ran it**: Started SonarQube Community 26.11.0.134175 in Docker on port 9000. Ran `./mvnw clean test jacoco:report -Dtest="*WhiteBoxTest"` (`clean` first so `target/jacoco.exec` was wiped and not contaminated by the 32 upstream integration tests in `src/test`), then `mvnw sonar:sonar`. CE task `07ae8f77-c571-4640-97c6-7253374e97ec` completed with SUCCESS.

**Key results to know cold**:
- **Which tests fed coverage to Sonar**: **Team tests only (75 white-box unit tests)**. Proof: `ExpenseController.java` has **0.0%** coverage (0/13 lines, 0/4 branches) in both JaCoCo XML and SonarQube.
- **Quality Gate**: OK (default Sonar way profile).
- **Bugs**: 0 (Reliability A).
- **Vulnerabilities**: 2 (Security D — both in upstream `SecurityConfig.java`, not ours):
  - CRITICAL `java:S4502` line 38: CSRF disabled. Safe because JWT Bearer tokens are used, not cookies.
  - MAJOR `java:S5122` line 117: CORS wildcard. Dev convenience; production would restrict origins.
- **Code Smells**: 0 / Technical Debt: 0 min / Maintainability: A.
- **Coverage (clean team-only)**: **56.9%** overall (**55.9%** line 257/460, **61.1%** branch 66/108) across all 33 classes. The 4 scoped classes remain **100%** (`ExpenseService` 107/107 L + 50/50 B, `AuthService` 32/32 L + 4/4 B, `RequestStatus` 14/14 L + 6/6 B, `ExpenseRequest` 9/9 L). The other 29 classes (controllers, filters, config) are at 0% because unit tests don't boot Spring/HTTP.
- **Duplication**: 0.0% — no copy-pasted blocks.
- **Complexity (whole project & file level)**: Whole project cyclomatic = **171**, cognitive = **53**. Sonar exposes complexity at **file level only** (`api/measures/component_tree` beneath a file returns 0 children); for `ExpenseService.java` (14 functions, 181 NCLOC): **cyclomatic = 45, cognitive = 22**.
- **Secrets check**: `.sonar-token.txt` and `.sonar/` are gitignored; zero tokens or passwords exist anywhere in git history or tracked files.

**Viva predictions**:
- If someone adds a nested `if-else` inside `assertCanDecide`: hand-computed V(G) increases by at least 1, `ExpenseService.java` file cyclomatic increases from 45, and file cognitive increases by more than 1 due to nesting penalty.
- If CSRF is re-enabled in `SecurityConfig`: vulnerability `S4502` disappears and security rating improves from D.
- If a Quality Gate condition requires e.g. 80% project-wide coverage on a unit-only run: it would FAIL at 56.9% unless upstream integration tests (`src/test`) also run (in Task 7 CI, all 107 tests run together).

---

## Task 6 — Mutation Testing (PIT + Custom Mutators)

**What mutation testing proves beyond line/branch coverage**: 100% coverage only proves tests *execute* every line and branch; mutation testing intentionally injects small faults ("mutants") into compiled bytecode and checks whether assertions actually *fail* when behaviour breaks.

**How a PIT plugin mutator works (viva summary)**:
- Custom mutators implement PIT's `MethodMutatorFactory` and are registered via Java's `ServiceLoader` (`META-INF/services/org.pitest.mutationtest.engine.gregor.MethodMutatorFactory`) in a JAR whose manifest includes `Implementation-Title` and `Implementation-Vendor`.
- PIT walks target `.class` files with ASM's `MethodVisitor`. When a mutator sees its target bytecode pattern, it registers a `MutationIdentifier`; during that mutant's test execution, `context.shouldMutate(id)` returns `true` and swaps the bytecode instructions in memory.

**Our 2 custom business-rule mutators (`tools/pit-custom-mutators/`)**:
1. `DROP_DEPARTMENT_CHECK` (`DropDepartmentCheckMutator.java`): Inside `ExpenseService.assertCanDecide`, pops the result of `Long.equals(me.getDepartmentId())` and `GOTO`s past the `throw ApiException.forbidden(...)`, letting any manager approve across departments (**1/1 killed**).
2. `SWAP_APPROVER_ROLE` (`SwapApproverRoleMutator.java`): Inside `RequestStatus.approverRole()`, swaps `Role.MANAGER` and `Role.FINANCE`, inverting stage ownership between `SUBMITTED` and `MANAGER_APPROVED` (**2/2 killed**).

**Key numbers**:
- Baseline (`DEFAULTS`): **71/79 (90%)** — 8 `VoidMethodCallMutator` survivors.
- `DEFAULTS` + custom (before -> after): **74/82 (90%)** -> **81/82 (99%)**.
- `STRONGER` + custom (before): **100/108 (93%)** (all 22 `RemoveConditionalMutator_EQUAL_IF` and 4 `SwitchMutator` mutants killed).
- Extended `ALL` + custom (before -> after): **312/333 (94%)** -> **328/333 (98%, test strength 99%)**, killing all 16 weak-assertion survivors via 4 new tests (`create_copiesTitleAndAllItemFields`, `approve_setsApprovalRequestBackReference`, `register_persistsEmailAndFullName`, `login_passesEmailAndPasswordToAuthenticationManager`), raising the team suite from 75 to **79 tests**.

**Why the 5 remaining mutants in `ALL` are equivalent / unreachable**:
- `ExpenseService.create:53` (`setStatus(DRAFT)`): `ExpenseRequest.java:69` already defaults `status = RequestStatus.DRAFT`, so skipping `setStatus(DRAFT)` changes nothing.
- `ExpenseService.get:95-96` (`getItems().size()`, `getApprovals().size()`): Hibernate lazy-loading touch calls whose return values are discarded; unit tests use eager `ArrayList`s.
- `ExpenseService.list:82` & `assertCanView:187` (`MatchException::<init>`): `javac` 21 emits unreachable default branches on exhaustive `Role` switches.

**Viva failure predictions**:
- If someone drops the department check in `assertCanDecide` (exact fault modeled by `DROP_DEPARTMENT_CHECK`): `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` and `reject_managerOtherDepartment_isForbidden` immediately fail.
- If someone swaps `Role.MANAGER` and `Role.FINANCE` in `RequestStatus.approverRole()` (modeled by `SWAP_APPROVER_ROLE`): `DomainWhiteBoxTest.transitionTable` and `approve_managerSameDepartment_isAllowed_D3_BtoFalse` / `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` immediately fail.

---

## Prompt Part 2 — Decision Tables, State Transitions, and Boundary Tests

**Task A (`05_decision_tables.md`)**:
- Documented all theoretical condition combinations for `assertCanDecide` (16 rows across C1–C4, 7 end-to-end paths), `submit` (8 rows across C1–C3, 4 reachable paths), and `update` (4 rows across C1–C2, 3 reachable paths), with verbatim code from `ExpenseService.java`.
- Explained short-circuiting: earlier `if` guards throw before later conditions execute, and `C3` (`needed == Role.MANAGER && !dept.equals(myDept)`) short-circuits to `false` at the `FINANCE` stage.
- All rows were already covered by `ExpenseServiceWhiteBoxTest` — no new tests needed.

**Task B (`06_state_transitions.md`)**:
- Built the 5-state × 5-event transition table (`DRAFT`, `SUBMITTED`, `MANAGER_APPROVED`, `FINANCE_APPROVED`, `REJECTED` vs `create/update`, `submit`, `approve`, `reject`) from `RequestStatus.java`.
- Verified every allowed transition (7 total) and at least one disallowed transition from each of the 5 states are covered by `ExpenseServiceWhiteBoxTest` — no new tests needed.

**Task C (`07_boundary_tests.md` & `ExpenseDtosValidationWhiteBoxTest.java`)**:
- Added **41 unit-level boundary and equivalence-class tests** using Jakarta Bean Validation `Validator` directly (no Spring context, no database), testing one invalid value per test (below, at, and above each constraint in `ExpenseDtos.java`).
- Covers `CreateRequest` (title, description, currency, items count: 18 tests), `ItemInput` (description, category, amount, incurredOn: 19 tests), and `DecisionInput` (comment: 4 tests).
- **Test-level note**: Member 2 tests the same limits through the HTTP API (integration level); these 41 tests are unit-level only and counted at the unit level only.

**Verification totals**:
- Team unit tests (`-Dtest="*WhiteBoxTest"`): **120** (`DomainWhiteBoxTest`: 15, `AuthServiceWhiteBoxTest`: 11, `ExpenseServiceWhiteBoxTest`: 53, `ExpenseDtosValidationWhiteBoxTest`: 41), 0 failures, 0 errors.
- JaCoCo 100% check on the 4 scoped classes: **passed** (`All coverage checks have been met.`).
- PIT (`DEFAULTS` + custom, threshold 95): **81/82 killed (99%), BUILD SUCCESS** (unchanged because PIT targets `service.*` and `domain.*`, while `ExpenseDtos` is in `web.dto`).
