# AI-Use Log — Member 1 (24i-3112)

This log records every task assistance from AI (AI Assistant), including the exact user prompt, tool invoked, purpose, tool output, and what was verified or changed, as required by project integrity rules.

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
- **JaCoCo Coverage Metric Verification** *(note: initial incremental run before `mvnw clean` measured 105/33 lines; clean `javac 21` compilation in Task 5 measured 107/32 lines — both 100%)*:
  - `com.sandy.expense.service.ExpenseService`: **100% line coverage** (105/105 incremental; 107/107 clean `javac`), **100% branch coverage** (50/50 branches).
  - `com.sandy.expense.service.AuthService`: **100% line coverage** (33/33 incremental; 32/32 clean `javac`), **100% branch coverage** (4/4 branches).
  - `com.sandy.expense.domain.RequestStatus`: **100% line coverage** (14/14 lines), **100% branch coverage** (6/6 branches).
  - `com.sandy.expense.domain.ExpenseRequest`: **100% line coverage** (9/9 lines), 0 branches.
- **JaCoCo Rule Check (`mvnw jacoco:check`)**:
  - `[INFO] All coverage checks have been met.` — **BUILD SUCCESS**.

### 5. What Was Checked or Changed
- **Checked**: Verified why `java` was initially missing from path in the tool shell; located Eclipse Temurin JDK 21 at `C:\Users\Z Book\AppData\Local\Programs\Eclipse Adoptium\jdk-21.0.13.10002-hotspot` from user registry `JAVA_HOME`.
- **Checked**: Examined whether any draft test assumptions mismatched source code. All 75 draft test assertions passed on the first run without needing behavioral modifications.
- **Changed**: Updated `pom.xml` to include `build-helper-maven-plugin` (to bind `tests/team/unit`), `jacoco-maven-plugin` (with `prepare-agent`, `report`, and `check` goals enforcing 100% on the 4 scoped classes), and `maven-surefire-plugin` with late-binding `@{argLine} -Dapi.version=1.44`.
  - The `-Dapi.version=1.44` property is taken verbatim from the README's Docker 29+ workaround block (see `docs/team/01_system_and_scope.md` §CI notes). The README documents that Testcontainers 1.21 negotiates a Docker API version below the `MinAPIVersion` that Docker 29 enforces; pinning `api.version=1.44` stops the daemon returning HTTP 400 on container start. On `ubuntu-latest` in GitHub Actions, Docker is provisioned by the runner image at version ≥ 29; the same `MinAPIVersion` restriction applies there, so the property is **required on CI too** and must not be removed.
- **Saved Evidence**: Copied full JaCoCo report to `docs/team/evidence/jacoco/` and preserved raw console test runs in `docs/team/evidence/02_whitebox_unit_test_run.txt` and `docs/team/evidence/02_jacoco_check.txt`.

---

## Task 2 — Correction Run (team-tests-only JaCoCo, verbatim quotes)

### 1. User Prompt (correction request)
> "(1) In the EMPTY_REQUEST justification you quoted code and a test name that do not exist in the repo. Re-open src/main/java/com/sandy/expense/service/ExpenseService.java and tests/team/.../ExpenseServiceWhiteBoxTest.java and quote them verbatim with file and line numbers. From now on, every code snippet in any doc must be copied from the real source, never paraphrased. (2) Re-run JaCoCo with ONLY the team tests (-Dtest="*WhiteBoxTest"), run jacoco:report and jacoco:check, and save that output separately as evidence. Tell me the coverage for the 4 target classes from team tests alone. If anything falls short, list the exact missed lines and branches. Don't change thresholds. Also confirm that the -Dapi.version=1.44 argLine you added to pom.xml is documented as a Docker 29 workaround, and tell me whether it affects CI on ubuntu-latest."

### 2. Tools Used
- `read_file`: Read `ExpenseService.java` lines 37–180 and `ExpenseServiceWhiteBoxTest.java` lines 150–596 to extract verbatim source with real line numbers.
- `run_command`: Ran `.\mvnw test jacoco:report -Dtest="*WhiteBoxTest"` and `.\mvnw jacoco:check` with output tee'd to `docs/team/evidence/03_team_tests_only_jacoco.txt` and `docs/team/evidence/03_team_tests_only_jacoco_check.txt`.
- `run_command`: Extracted per-class metrics from `target/site/jacoco/jacoco.xml` using PowerShell XML query.
- `run_command`: Searched `README.md` for the `api.version` / `1.44` context.

### 3. Purpose
- Correct previously paraphrased/hallucinated code snippets in the viva notes by reading and quoting the real source files.
- Produce a separate JaCoCo evidence run covering **only** the 75 team tests (no upstream integration tests) to prove the team tests alone supply 100% line and branch coverage on the 4 scoped classes.
- Document the `-Dapi.version=1.44` property's origin and CI applicability.

### 4. Output Summary

**Team-only test run (`mvnw test jacoco:report -Dtest="*WhiteBoxTest"`):**
- `DomainWhiteBoxTest`: 15 tests, 0 failures.
- `AuthServiceWhiteBoxTest`: 9 tests, 0 failures.
- `ExpenseServiceWhiteBoxTest`: 51 tests, 0 failures.
- **Total: 75 tests run, 0 failures, BUILD SUCCESS.**

**Coverage from team tests only (extracted from `target/site/jacoco/jacoco.xml`):**

| Class | Type | Covered | Missed | Total | % |
|-------|------|---------|--------|-------|---|
| `RequestStatus` | LINE | 14 | 0 | 14 | **100%** |
| `RequestStatus` | BRANCH | 6 | 0 | 6 | **100%** |
| `ExpenseRequest` | LINE | 9 | 0 | 9 | **100%** |
| `ExpenseService` | LINE | 105 *(107 clean)* | 0 | 105 *(107 clean)* | **100%** |
| `ExpenseService` | BRANCH | 50 | 0 | 50 | **100%** |
| `AuthService` | LINE | 33 *(32 clean)* | 0 | 33 *(32 clean)* | **100%** |
| `AuthService` | BRANCH | 4 | 0 | 4 | **100%** |

No missed lines or branches on any of the 4 target classes. The check gate passes unchanged.

**`jacoco:check` output (team-only exec):**
```
[INFO] All coverage checks have been met.
[INFO] BUILD SUCCESS
```

**`-Dapi.version=1.44` — origin and CI impact:**
- The property is documented in the README (verbatim):
  > **Docker 29+**: Testcontainers 1.21 negotiates an API version below the `MinAPIVersion` that Docker 29 enforces, so the daemon answers `400` and every container start fails. Until Testcontainers ships a fix, pin the API version for the test JVM:
  > `./mvnw test -DargLine="-Dapi.version=1.44 -Ddocker.host=unix://$HOME/.docker/run/docker.sock"`
- In `pom.xml` we wired it into `maven-surefire-plugin` as `<argLine>@{argLine} -Dapi.version=1.44</argLine>` so it applies to every `mvnw test` invocation without a command-line override.
- **Effect on CI (`ubuntu-latest`)**: the GitHub Actions `ubuntu-latest` runner also ships Docker ≥ 29; the same `MinAPIVersion` restriction applies there, so the property **is required on CI** and must remain. Removing it from `pom.xml` would cause the Testcontainers integration tests to fail on CI with HTTP 400 from the Docker daemon. The `-Ddocker.host=...` socket flag from the README is a macOS-specific path; the `api.version` pin alone is sufficient on Linux runners.

### 5. What Was Checked or Changed
- **Checked**: Read `ExpenseService.java` lines 127–141 and 166–180; confirmed the actual throw at line 136 is `ApiException.badRequest("EMPTY_REQUEST", "Add at least one line item before submitting")` — different from what was previously paraphrased in the docs.
- **Checked**: Read `ExpenseServiceWhiteBoxTest.java` lines 352–364; confirmed the actual test name is `submit_draftWithNoItems_isRejected_BR1` and the `asserting` code is as copied above — different from the previously fabricated name `submit_emptyItems_throwsEmptyRequest`.
- **Changed**: Rewrote the EMPTY_REQUEST and assertCanDecide sections in `viva_notes_member1.md` using verbatim text with explicit file and line references.
- **Changed**: Updated the Viva Failure Prediction section to use real test method names from the source (`approve_managerOtherDepartment_isForbidden_D3_BtoTrue`, `approve_managerOnOwnRequest_isForbidden_D4_true`, `approve_financeOnOwnRequest_isForbidden_D4_true`) rather than invented names.
- **Saved Evidence**: `docs/team/evidence/03_team_tests_only_jacoco.txt` and `docs/team/evidence/03_team_tests_only_jacoco_check.txt`.

---

## Task 3 — System Description and Scope (`docs/team/01_system_and_scope.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-25 |
| Purpose | Write `docs/team/01_system_and_scope.md`: project identity, install commands, DB, roles, requirements, and 4 business rules, all with verbatim code snippets and file+line references |
| Output | 278-line Markdown document covering project identity, install/start/reset commands, DB schema (Flyway V1+V2), role enforcement (HTTP + service layer), 13 requirements (REQ-A1–A4, REQ-E1–E8, REQ-AP1–AP4), and 4 business rules (BR1–BR4) |
| What was checked | Every code snippet was read verbatim from the real source files (`ExpenseService.java`, `ExpenseDtos.java`, `ExpenseController.java`, `V1__init_schema.sql`, `V2__add_finance_role.sql`, `DataSeeder.java`) with line numbers verified by `Get-Content` and line-range reads. No requirement was invented; each is traceable to a specific method or annotation in the codebase. |
| What was changed | None — doc is a new file. The previous session's fabricated code snippets are not present; all quotes in this document were taken from the live repo. |

**Prompt used (paraphrased)**: "Do Task 3 (docs/team/01_system_and_scope.md). Copy every code snippet verbatim from the real source with file and line numbers. Take requirements only from the real code or README."

---

## Task 4 — MC/DC and CFG Analysis (`docs/team/03_mcdc_and_cfg.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-25 |
| Purpose | Write `docs/team/03_mcdc_and_cfg.md`: CFG of `assertCanDecide`, cyclomatic complexity (both E−N+2 and decisions+1), full MCC table, MC/DC independence pairs mapped to real test method names, BR2/BR4 decision tables, BR3 state transition table |
| Output | 321-line Markdown document (after Task 5 CFG reconciliation) with ASCII CFG, 11-node/15-edge inventory, V(G)=6 by both formulas (`1 + 4 ifs + 1 && = 6` and `15 − 11 + 2 = 6`), 7-row MCC table, MC/DC pairs for D1/D2/D3-A/D3-B/D4 each referencing exact test method names and line numbers in `ExpenseServiceWhiteBoxTest.java`, and three tables (BR2 decision, BR4 decision, BR3 state transitions) |
| What was checked | Source of `assertCanDecide` read verbatim from `ExpenseService.java` lines 162–180. Test method names and line numbers verified against `tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java`. No test name or line number was inferred; every reference was read from the file. Cyclomatic complexity computed by both formulas and cross-checked. |
| What was changed | None initially; later expanded in the Task 5 Correction Pass to split short-circuit `&&` and collapse `[EXIT]` so both formulas equal 6. |

**Prompt used (paraphrased)**: "For Task 4, draw the CFG of `ExpenseService.assertCanDecide`, list nodes and edges, compute cyclomatic complexity step by step both ways (E−N+2 and decisions+1). Build the full MCC table and MC/DC independence pairs, map each pair to the exact test method names. Add a decision table for BR2 and BR4 and a state transition table for BR3."


---

## Task 5 — SonarQube Static Analysis (`docs/team/02_static_analysis.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-25 |
| Purpose | Run SonarQube Community scan on the project, capture all metrics (bugs, vulnerabilities, code smells, hotspots, coverage, complexity, duplication, ratings, tech debt, quality gate), and write `docs/team/02_static_analysis.md` explaining each metric in plain words |
| Output | SonarQube Community Build 26.11.0.134175 running on Docker port 9000. `sonar-maven-plugin` 5.9.0.7382 added to `pom.xml`. Final clean scan completed (CE task `07ae8f77-c571-4640-97c6-7253374e97ec`, SUCCESS). All metrics captured via REST API and saved to `docs/team/evidence/05_sonar_measures.txt` and `05_sonar_scan.txt`. `02_static_analysis.md` written (172 lines after Task 5 Correction Pass). |
| What was checked | Metrics pulled live from `http://localhost:9000/api/measures/component` and `/api/issues/search` after CE task reported SUCCESS. No numbers were fabricated — every value in the doc comes from the API responses captured in evidence files. The two vulnerabilities (S4502 and S5122) were verified against their actual rule IDs and descriptions from SonarQube. |
| What was changed | `pom.xml`: added `sonar-maven-plugin` 5.9.0.7382 and a `sonar` profile with standard properties. `sonar-project.properties` written (for reference). `.sonar-token.txt` written (gitignored). |

**Prompts used (paraphrased)**: "Do Task 5 (SonarQube). Start SonarQube in Docker, run sonar:sonar feeding the JaCoCo XML. Capture complexity, duplication, smells, bugs, vulnerabilities, coverage, tech debt, ratings. Explain each metric in plain words in docs/team/02_static_analysis.md."

---

## Task 5 Correction Pass — Clean JaCoCo Isolation & Complexity Reconciliation (`docs/team/02_static_analysis.md`, `docs/team/03_mcdc_and_cfg.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-25 |
| Purpose | Fix three discrepancies identified before starting Task 6: (1) wipe `target/` with `mvnw clean` before running team-only tests so `jacoco.exec` does not append onto the 107-test run, (2) verify whether SonarQube exposes per-method complexity and replace estimated per-method figures with real file-level measures + recount `assertCanDecide` by hand as `1 + 4 ifs + 1 && = 6`, (3) explicitly state which tests produced coverage fed to Sonar and verify zero secrets/tokens are committed. |
| Output | Re-ran `./mvnw clean test jacoco:report -Dtest="*WhiteBoxTest"` (75 tests, 0 failures) and `mvnw jacoco:check` (`All coverage checks have been met.`), then re-ran `mvnw sonar:sonar` (CE task `07ae8f77-c571-4640-97c6-7253374e97ec`, SUCCESS). Saved clean outputs in `docs/team/evidence/06_team_only_clean_jacoco.txt`, `06_team_only_clean_jacoco_check.txt`, `06_team_only_clean_jacoco.xml`, and updated `05_sonar_measures.txt` & `05_sonar_scan.txt`. Updated `03_mcdc_and_cfg.md`, `02_static_analysis.md`, and `viva_notes_member1.md`. |
| What was checked | (1) Extracted clean JaCoCo XML totals: overall LINE 257/460 (55.87%), BRANCH 66/108 (61.11%); 4 scoped classes still 100% (`ExpenseService` 107/107 L + 50/50 B, `AuthService` 32/32 L + 4/4 B, `RequestStatus` 14/14 L + 6/6 B, `ExpenseRequest` 9/9 L — note that earlier pre-`clean` Task 2 runs showed 105/105 and 33/33 from incremental compilation before `mvnw clean` recompiled all classes cleanly with `javac 21`); `ExpenseController` 0/13 lines (0%) and 0/4 branches (0%), proving HTTP integration tests were excluded. (2) Queried `api/measures/component_tree` under `ExpenseService.java` (returned 0 child components — confirming SonarQube exposes file-level complexity only: `ExpenseService.java` cyclomatic = 45, cognitive = 22, 14 functions). Expanded CFG in `03_mcdc_and_cfg.md` to split short-circuit `&&` (`N5a`, `N5b`) with collapsed `[EXIT]` (`N=11, E=15 -> E-N+2 = 6`), matching `1 + 4 ifs + 1 && = 6`. (3) Verified `git ls-files .sonar-token.txt` and `git grep sqa_` both return empty, and `.gitignore` ignores `.sonar-token.txt` and `.sonar/`. |
| What was changed | Updated `docs/team/03_mcdc_and_cfg.md` (CFG nodes/edges, `V(G)=6` both ways, removed estimated per-method Sonar figures), `docs/team/02_static_analysis.md` (clean coverage 56.9% overall, `ExpenseController` 0.0% proof, file-level complexity table for `ExpenseService.java`, token security statement), `docs/team/viva_notes_member1.md` (updated Task 4/5 notes and fixed UTF-8 punctuation), `docs/team/ai_use_member1.md` (reconciled doc line counts and pre/post-clean JaCoCo line counts). |

**Prompt used (paraphrased)**: "Before Task 6: (1) Run `.\mvnw clean test -Dtest="*WhiteBoxTest" jacoco:report` so `target/` is wiped first; report overall totals, 4 scoped classes, and `ExpenseController` coverage near 0%. (2) Show if Sonar gives per-method complexity; if not, remove those figures, show real file-level values for `ExpenseService.java`, and recount the method by hand (`1 + 4 ifs + 1 && = 6`). (3) State clearly which tests fed coverage to Sonar and confirm no Sonar token/password is committed."

---

## Task 6 — Mutation Testing with PIT & Custom Business-Rule Mutators (`docs/team/04_mutation_testing.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-25 |
| Purpose | Configure PIT (`pitest-maven:1.30.2` + `pitest-junit5-plugin:1.2.3`) against team tests only, build 2 custom business-rule mutators in `tools/pit-custom-mutators/`, run `DEFAULTS`, `DEFAULTS+custom`, `STRONGER+custom`, and `ALL+custom`, classify >= 15 survivors, write tests to kill killable survivors, and report before/after scores in `docs/team/04_mutation_testing.md`. |
| Output | (1) `tools/pit-custom-mutators/`: `DropDepartmentCheckMutator` (`DROP_DEPARTMENT_CHECK`, BR2) and `SwapApproverRoleMutator` (`SWAP_APPROVER_ROLE`, BR3/BR4) registered via `ServiceLoader`, with `Implementation-Title`/`Version`/`Vendor` manifest entries. (2) Measured scores before fix: `DEFAULTS` baseline **71/79 (90%)**, `DEFAULTS+custom` **74/82 (90%)** (`DROP_DEPARTMENT_CHECK` 1/1 killed, `SWAP_APPROVER_ROLE` 2/2 killed), `STRONGER+custom` **100/108 (93%)**, extended `ALL+custom` **312/333 (94%)** (19 `SURVIVED` + 2 `NO_COVERAGE`). (3) Classified all 21 non-killed mutants (5 equivalent/unreachable, 16 weak assertions) and added 4 tests bringing team suite to 79 tests. (4) Measured scores after fix: `DEFAULTS+custom` **81/82 (99%)**, `ALL+custom` **328/333 (98%, 99% test strength)**. Written report: `docs/team/04_mutation_testing.md`; raw outputs archived under `docs/team/evidence/07_pit_*` and `docs/team/evidence/pit-*/`. |
| What was checked | Resolved PIT's initial `No implementation title/vendor in manifest` error by adding explicit `<manifestEntries>` in `tools/pit-custom-mutators/pom.xml`. Verified both custom mutators generated real bytecode mutants and were killed 100% by existing team tests. Parsed `mutations.xml` from `ALL+custom` to confirm every survivor line number against `ExpenseService.java`, `AuthService.java`, and `ExpenseRequest.java` (confirming `status = RequestStatus.DRAFT` default initialization at `ExpenseRequest.java:69`). Re-ran both PIT `DEFAULTS+custom` and clean team-only JaCoCo check (`79` tests passing, `All coverage checks have been met.`) after final test additions. |
| What was changed | Created `tools/pit-custom-mutators/` Maven module; updated `pom.xml` (`pitest-maven`, `pitest-junit5-plugin`, `pit-custom-mutators` dependency, `DEFAULTS` + custom mutators); added 2 tests in `ExpenseServiceWhiteBoxTest.java` and 2 tests in `AuthServiceWhiteBoxTest.java`; created `docs/team/04_mutation_testing.md`; updated `docs/team/viva_notes_member1.md` and `docs/team/ai_use_member1.md`. |

**Prompts used (paraphrased)**: "Proceed to Task 6 (PIT mutation testing). Show baseline score first, then: (1) build 2 custom mutators in `tools/pit-custom-mutators/` and explain how a PIT plugin mutator works in simple words; (2) run `DEFAULTS` + custom and a stronger group, keeping `DEFAULTS` 90% as baseline and reporting extended runs separately; (3) classify at least 15 survivors as equivalent / missing test / weak assertion; (4) add tests in `tests/team/unit` to kill killable ones and report before/after scores without weakening tests or excluding code."

---

## Prompt Part 2 — Decision Tables, State Transitions, and Boundary Tests (`docs/team/05_decision_tables.md`, `06_state_transitions.md`, `07_boundary_tests.md`, `ExpenseDtosValidationWhiteBoxTest.java`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-26 |
| Purpose | Produce full decision tables for `assertCanDecide`, `submit`, and `update` (Task A), full 5-state transition table with gap analysis (Task B), and Jakarta Bean Validation boundary/equivalence unit tests for `ExpenseDtos` (Task C), then verify full team suite + JaCoCo 100% check + PIT (`DEFAULTS` + custom, threshold 95). |
| Output | Created `docs/team/05_decision_tables.md`, `docs/team/06_state_transitions.md`, `docs/team/07_boundary_tests.md`, and `tests/team/unit/com/sandy/expense/web/dto/ExpenseDtosValidationWhiteBoxTest.java` (41 unit-level boundary tests; named `*WhiteBoxTest` so `-Dtest="*WhiteBoxTest"` in CI and local runs is identical). Ran `.\mvnw.cmd clean test jacoco:report jacoco:check -Dtest="*WhiteBoxTest" --no-transfer-progress` (**120 tests run, 0 failures, 0 errors**, `All coverage checks have been met.`) and `.\mvnw.cmd test-compile org.pitest:pitest-maven:mutationCoverage "-DmutationThreshold=95" --no-transfer-progress` (**81/82 killed, 99%, BUILD SUCCESS**). |
| What was checked | Read `ExpenseService.java`, `RequestStatus.java`, `ExpenseDtos.java`, and `ExpenseServiceWhiteBoxTest.java` verbatim with exact line numbers. Verified all decision-table rows (16 rows / 7 end-to-end paths for `assertCanDecide`, 8 rows for `submit`, 4 rows for `update`) and all state transitions (all 7 allowed transitions + disallowed transitions from every state) were already covered by existing tests in `ExpenseServiceWhiteBoxTest`. Verified each boundary test in `ExpenseDtosValidationWhiteBoxTest` tests one invalid value per test (below, at, above) using Jakarta Bean Validation `Validator` with no Spring context or DB. |
| What was changed | Added `docs/team/05_decision_tables.md`, `docs/team/06_state_transitions.md`, `docs/team/07_boundary_tests.md`, and `ExpenseDtosValidationWhiteBoxTest.java` (41 tests, bringing team unit suite from 79 to 120 tests). Updated `docs/team/ai_use_member1.md` and `docs/team/viva_notes_member1.md`. |

**Prompts used (paraphrased)**: "Decision tables (`05_decision_tables.md`), state transition table (`06_state_transitions.md`), and boundary value + equivalence tests (`ExpenseDtosValidationWhiteBoxTest.java` + `07_boundary_tests.md`) on branch `member1/decision-state-boundary-tests`, then run full team tests with `-Dtest="*WhiteBoxTest"`, JaCoCo check, and PIT (threshold 95)."

---

## Task 7 Demonstration — Blocked PR, Fix PR & Evidence (`docs/team/09_blocked_and_fix_pr.md`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-26 |
| Purpose | Demonstrate the CI quality gate on a blocked PR (`demo/blocked-drop-department-check`, PR #3), confirm and fix the `currency = "123"` validation defect (`fix/currency-validation`, PR #5 / Issue #4) with a red Commit 1 followed by a green Commit 2, and archive all CI logs/screenshots in `docs/team/09_blocked_and_fix_pr.md`. |
| Output | (1) `demo/blocked-drop-department-check` (`34b7179`, PR #3, run `45770054227`): failed `Run team tests with JaCoCo report and 100 % check` (`Tests run: 120, Failures: 3`). (2) `fix/currency-validation` Commit 1 (`7b96f70`, PR #5, run `45794816172`): failed `Run team tests with JaCoCo report and 100 % check` (`Tests run: 121, Failures: 1`, `currency_numeric123_isInvalid`). (3) `fix/currency-validation` Commit 2 (`2252ae8`, merged `0dfa6ce`): added `@Pattern(regexp = "[A-Za-z]{3}")` in `ExpenseDtos.java` + 4 tests (`"@@@"`, `"US1"`, `"usd"`, `"USD"`), passing all CI gates (`125` team tests, `157` full suite, SonarQube `SQE-CI`, PIT `81/82 = 99%`). (4) Archived `10_*`, `11_*`, `12_*` screenshots/logs and wrote `docs/team/09_blocked_and_fix_pr.md` on `docs/evidence-blocked-and-fix-pr`. |
| What was checked | Searched all tracked files in `src/`, `frontend/`, and `tests/` for `currency` references to ensure `@Pattern(regexp = "[A-Za-z]{3}")` would not break seeders, migrations, UI, or existing tests. Extracted verbatim log lines from `10_blocked_pr_logs.zip`, `11_fix_pr_before_logs.zip`, and `12_fix_pr_after_logs.zip` and verified run summary metadata from `12_fix_pr_after_run_summary.png`. |
| What was changed | Created `docs/team/issues/currency_validation.md` and `ExpenseDtos.java` / `ExpenseDtosValidationWhiteBoxTest.java` changes (merged via PR #5); created `docs/team/09_blocked_and_fix_pr.md`; staged `docs/team/evidence/10_*`, `11_*`, `12_*` and updated `docs/team/ai_use_member1.md`. |

**Prompts used (paraphrased)**: "Do the blocked PR (`demo/blocked-drop-department-check`), the fix PR (`fix/currency-validation`: failing test commit 1, `@Pattern` fix + 4 tests commit 2), and archive the `10_`, `11_`, `12_` evidence and `docs/team/09_blocked_and_fix_pr.md` on `docs/evidence-blocked-and-fix-pr`."

---

## Prompt Part 3 — Use Cases UC1 & UC2 + Playwright E2E Automation (`docs/team/uc/`, `tests/team/e2e/`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-26 |
| Purpose | Inspect the real React UI and Spring Boot API, write use case specifications (`UC1_submit_draft.md`, `UC2_create_draft.md`), record the missing edit UI observation (`docs/team/issues/ui_no_edit_form.md`), and automate all 10 flows in Playwright (`tests/team/e2e/`) with display + independent postcondition assertions. |
| Output | (1) `docs/team/issues/ui_no_edit_form.md`: recorded that `PUT /api/requests/{id}` exists in `ExpenseController.java` L64-70 but has no frontend edit form (covered by Member 2 at API level). (2) `docs/team/uc/UC1_submit_draft.md` (5 flows: `UC1_M`, `UC1_A1`, `UC1_A2`, `UC1_E1`, `UC1_E2`) and `docs/team/uc/UC2_create_draft.md` (5 flows: `UC2_M`, `UC2_A1`, `UC2_A2`, `UC2_E1`, `UC2_E2`). (3) `tests/team/e2e/` (`package.json`, `playwright.config.ts` with `workers: 1` Chromium, `.gitignore`, `tests/helpers.ts`, `tests/uc1-submit.spec.ts`, `tests/uc2-create.spec.ts`). (4) Ran all 10 tests twice against the live app (`localhost:5173` + `localhost:8081`): **10 passed (15.9s)** in `docs/team/evidence/uc/run1.txt` and **10 passed (15.4s)** in `docs/team/evidence/uc/run2.txt`. |
| What was checked | Inspected `App.tsx`, `Login.tsx`, `NewRequest.tsx`, `RequestDetail.tsx`, `RequestList.tsx`, `api.ts`, `auth.tsx`, `types.ts`, `ui.tsx`, `ExpenseController.java`, `ExpenseService.java`, `ExpenseDtos.java`, and `GlobalExceptionHandler.java`. Confirmed that `<label>` tags in the UI are sibling elements without `for` attributes, so `fieldByLabel` scopes to `label` → parent `div` → `input/textarea/select` without modifying upstream frontend code. Confirmed live error div text for currency `"123"` is `"Request validation failed"`. |
| What was changed | Added `docs/team/issues/ui_no_edit_form.md`, `docs/team/uc/UC1_submit_draft.md`, `docs/team/uc/UC2_create_draft.md`, `tests/team/e2e/*`, `docs/team/evidence/uc/run1.txt`, `docs/team/evidence/uc/run2.txt`, and updated `docs/team/ai_use_member1.md` and `docs/team/viva_notes_member1.md`. |

**Prompts used (paraphrased)**: "Inspect the real app for UC1/UC2, record the missing edit UI as an observation, write UC1 (submit draft) and UC2 (create draft) specs with M/A1/A2/E1/E2 flows, automate all 10 flows in Playwright (`workers: 1`), run twice, save evidence, and recommend how to wire CI without editing `quality-gate`."

---

## Prompt Part 4 — Consistency Audit, Hand-Off Notes, PDF Section & Prompt Archive (`member1/final-docs`)

| Field | Value |
|---|---|
| Tool | Generative AI Assistant (LLM) |
| Date | 2026-11-27 |
| Purpose | Audit all `docs/team/` numbers and evidence links, update `05_handoff_notes.md`, write `Member1_PDF_Section.md`, archive the exact prompt files in `docs/team/prompts/`, and document both AI tools honestly. |
| Output | Verified 0 missing evidence files and 5 PR/run URLs; identified and corrected `07_boundary_tests.md` (`41 → 46`, baseline 41 + 5 PR #5 currency tests) and `viva_notes_member1.md` (`120 → 125`); added Sonar scan commit/date and re-measurement note to `02_static_analysis.md`; updated `05_handoff_notes.md` (with verified PIT `81/82 = 99%` run); created `Member1_PDF_Section.md`; archived prompt files under `docs/team/prompts/`. |
| What was checked | Ran Python audit script across all 16 markdown files in `docs/team/`; ran PIT (`mvnw -f tools/pit-custom-mutators/pom.xml clean install` + `mvnw test-compile org.pitest:pitest-maven:mutationCoverage "-DmutationThreshold=95"`) confirming `81/82 (99%)` after all merges. |
| What was changed | Updated `02_static_analysis.md`, `05_handoff_notes.md`, `07_boundary_tests.md`, `viva_notes_member1.md`, `ai_use_member1.md`; created `Member1_PDF_Section.md` and `docs/team/prompts/*`. |

---

## Summary of Both AI Tools Used (Honesty & Attribution)

| Tool | Role & Purpose | Output Used | What Member 1 Checked or Changed |
|---|---|---|---|
| **AI Assistant** (Google DeepMind) | Code editing, test generation (white-box unit, DTO boundary, Playwright E2E), Maven/JaCoCo/Sonar/PIT/Playwright execution, documentation, and consistency checks | Unit tests (`tests/team/unit/`), Playwright suite (`tests/team/e2e/`), custom PIT mutators (`tools/pit-custom-mutators/`), CI workflow (`.github/workflows/ci.yml`), and `docs/team/*.md` | Checked all code quotes against real line numbers, ran every test/build/CI command directly, caught and corrected initial hallucinations/mismatches (e.g. `EMPTY_REQUEST`, decision path count `7`, `09_blocked_and_fix_pr.md` log line verification, `07_boundary_tests.md` `41 → 46`). |
| **Claude** (Anthropic chat assistant) | Used by Member 1 in chat to draft the structured AI Assistant prompts, review AI Assistant's reports, catch gaps/inconsistencies, and explain SQE concepts | Prompt specifications archived in [`docs/team/prompts/`](prompts/) (`ANTIGRAVITY_PROMPT_MEMBER1.md`, `ANTIGRAVITY_PROMPT_PART2.md`, `ANTIGRAVITY_PROMPT_PART3_USE_CASES.md`, `ANTIGRAVITY_PROMPT_4_5_AND_FOLLOWUP_MESSAGES.md`) | Reviewed every prompt against course requirements and repo state before sending to AI Assistant; verified AI Assistant's outputs against raw logs and GitHub Actions runs. |

Smaller follow-up corrections typed in chat are not archived as files.
