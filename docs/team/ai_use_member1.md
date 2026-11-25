# AI-Use Log — Member 1 (24i-3112)

This log records every task assistance from AI (Antigravity), including the exact user prompt, tool invoked, purpose, tool output, and what was verified or changed, as required by project integrity rules.

---

## Task 2: Build Wiring & Initial Test Suite Execution

### 1. User Prompt
> "Task 1 (baseline) is already done: all 32 upstream tests pass on my Windows PC with Java 21 and Docker, and evidence is in docs/team/evidence. Start at task 2. First compile and run my three test files in tests/team/unit, and show me any failures before changing anything.
> 2. Build wiring in pom.xml. Add `build-helper-maven-plugin` so `tests/team/unit` is a test source root. Add the JaCoCo plugin (prepare-agent, report including XML, and a `check` rule). Scope for the 100% target: `com.sandy.expense.service.ExpenseService`, `AuthService`, `domain.RequestStatus`, `domain.ExpenseRequest`. Run the team tests plus upstream tests and report line and branch coverage. Justify any uncovered line in writing. Example already known: the `EMPTY_REQUEST` branch of `submit` is unreachable through HTTP because `CreateRequest.items` is `@NotEmpty`, but it is reachable at service level."

### 2. Tools Used
- `edit_file`: Configured `build-helper-maven-plugin` (v3.6.0), `jacoco-maven-plugin` (v0.8.12), and `maven-surefire-plugin` with `@{argLine} -Dapi.version=1.44` in `pom.xml`.
- `run_command`: Ran `mvnw test-compile`, `mvnw test -Dtest="*WhiteBoxTest"`, `mvnw test`, and `mvnw jacoco:check`.
- `manage_task` / `schedule`: Monitored background execution of maven processes.

### 3. Purpose
1. Add `tests/team/unit` as an official Maven test source directory using `build-helper-maven-plugin`.
2. Compile and run the draft white-box test files (`DomainWhiteBoxTest`, `AuthServiceWhiteBoxTest`, `ExpenseServiceWhiteBoxTest`) without any prior source modification to identify draft errors or mismatches.
3. Wire JaCoCo with `prepare-agent`, `report` (XML + HTML), and `check` rules enforcing 100% line and branch coverage on the four designated target classes: `ExpenseService`, `AuthService`, `RequestStatus`, and `ExpenseRequest`.
4. Validate that all 107 tests (32 upstream + 75 team tests) execute and pass, verifying coverage against the JaCoCo metric thresholds.

### 4. Output Summary
- **Test Compilation (`mvnw test-compile`)**: Successfully compiled all 13 test source files (including 3 team test classes) targeting Java 21.
- **Initial White-Box Unit Test Execution (`mvnw test -Dtest="*WhiteBoxTest"`)**:
  - `DomainWhiteBoxTest`: 15 tests, 0 failures, 0 errors, 0 skipped.
  - `AuthServiceWhiteBoxTest`: 9 tests, 0 failures, 0 errors, 0 skipped.
  - `ExpenseServiceWhiteBoxTest`: 51 tests, 0 failures, 0 errors, 0 skipped.
  - Total: **75 tests run, 0 failures, 0 errors**.
- **Combined Test Run (Upstream + Team Unit Tests: `mvnw test`)**:
  - Total: **107 tests run, 0 failures, 0 errors, 0 skipped**.
- **JaCoCo Coverage Metric Verification**:
  - `com.sandy.expense.service.ExpenseService`: **100% line coverage** (105/105 lines), **100% branch coverage** (50/50 branches).
  - `com.sandy.expense.service.AuthService`: **100% line coverage** (33/33 lines), **100% branch coverage** (4/4 branches).
  - `com.sandy.expense.domain.RequestStatus`: **100% line coverage** (14/14 lines), **100% branch coverage** (6/6 branches).
  - `com.sandy.expense.domain.ExpenseRequest`: **100% line coverage** (9/9 lines), 0 branches.
- **JaCoCo Rule Check (`mvnw jacoco:check`)**:
  - `[INFO] All coverage checks have been met.` — **BUILD SUCCESS**.

### 5. What Was Checked or Changed
- **Checked**: Verified why `java` was initially missing from path in the tool shell; located Eclipse Temurin JDK 21 at `C:\Users\Z Book\AppData\Local\Programs\Eclipse Adoptium\jdk-21.0.13.10002-hotspot` from user registry `JAVA_HOME`.
- **Checked**: Examined whether any draft test assumptions mismatched source code. All 75 draft test assertions passed on the first run without needing behavioral modifications.
- **Changed**: Updated `pom.xml` to include `build-helper-maven-plugin` (to bind `tests/team/unit`), `jacoco-maven-plugin` (with `prepare-agent`, `report`, and `check` goals enforcing 100% on the 4 scoped classes), and `maven-surefire-plugin` with late-binding `@{argLine} -Dapi.version=1.44`.
- **Saved Evidence**: Copied full JaCoCo report to `docs/team/evidence/jacoco/` and preserved raw console test runs in `docs/team/evidence/02_whitebox_unit_test_run.txt` and `docs/team/evidence/02_jacoco_check.txt`.
