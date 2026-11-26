# Member 1 (24i-3112) — Quality Engineering Summary

## 1. System and Scope

The system under test is **Expense Approval**, a full-stack reimbursement workflow application (Spring Boot 4.1 / Java 21 backend, PostgreSQL 16 + Flyway schema, React 19 + TypeScript frontend) with three roles (`EMPLOYEE`, `MANAGER`, `FINANCE`) and a five-state lifecycle (`DRAFT` → `SUBMITTED` → `MANAGER_APPROVED` → `FINANCE_APPROVED` / `REJECTED`).
Source: [`docs/team/01_system_and_scope.md`](01_system_and_scope.md).

Member 1 scoped white-box unit testing, JaCoCo enforcement, static analysis, PIT mutation testing, CI quality gating, and UC1/UC2 Playwright E2E automation on the core domain and service layer (`ExpenseService`, `AuthService`, `RequestStatus`, `ExpenseRequest`) plus `ExpenseDtos` validation.

---

## 2. Static Analysis (SonarQube)

Scanned with SonarQube Community `26.11.0.134175` using team-only JaCoCo XML (`75` unit tests at scan time; `ExpenseController` at `0.0%` proves integration tests were excluded).
Evidence: [`docs/team/evidence/05_sonar_measures.txt`](evidence/05_sonar_measures.txt), [`docs/team/02_static_analysis.md`](02_static_analysis.md).

| Metric | Measured Value | Plain-Language Meaning |
|---|---|---|
| Quality Gate | **OK** (`SQE-CI`: PASSED) | All quality gate thresholds met |
| Bugs | **0** (Reliability **A**) | No static reliability defects |
| Vulnerabilities | **2** (Security **D**) | Both upstream in `SecurityConfig.java` (`S4502` CSRF disabled for stateless JWT; `S5122` CORS wildcard) |
| Code Smells | **0** (0 min debt, Rating **A**) | Clean maintainability |
| Overall Coverage | **56.9%** (55.9% line, 61.1% branch) | Unit tests only; scoped classes are 100% |
| Duplication | **0.0%** | No duplicated blocks |
| Cyclomatic / Cognitive Complexity | **171 / 53** (project) | `ExpenseService.java` file-level: **45 / 22** |

**Hand-calculated vs Sonar complexity**: SonarQube exposes complexity at **file level only** (`ExpenseService.java` = 45 cyclomatic, 22 cognitive). Hand-calculation on `ExpenseService.assertCanDecide` gives `V(G) = E - N + 2 = 15 - 11 + 2 = 6`, and `predicates + 1 = 4 ifs + 1 && + 1 = 6`.
Evidence: [`docs/team/03_mcdc_and_cfg.md`](03_mcdc_and_cfg.md), [`docs/team/evidence/05_sonar_measures.txt`](evidence/05_sonar_measures.txt).

---

## 3. White-Box Testing (JaCoCo, MCC, MC/DC)

- **JaCoCo 100% gate** (enforced in `pom.xml`): `ExpenseService` (100% line/branch), `AuthService` (100% line/branch), `RequestStatus` (100% line/branch), `ExpenseRequest` (100% line).
  Evidence: [`docs/team/evidence/06_team_only_clean_jacoco.txt`](evidence/06_team_only_clean_jacoco.txt), [`docs/team/evidence/06_team_only_clean_jacoco_check.txt`](evidence/06_team_only_clean_jacoco_check.txt).
- **MCC & MC/DC (`assertCanDecide`)**: 7 feasible condition combinations (short-circuit `if` chain prevents reaching later guards when earlier ones throw) and full MC/DC independence pairs for D1, D2, D3-A, D3-B, and D4 mapped to `ExpenseServiceWhiteBoxTest`.
  Evidence: [`docs/team/03_mcdc_and_cfg.md`](03_mcdc_and_cfg.md), [`docs/team/05_decision_tables.md`](05_decision_tables.md), [`docs/team/06_state_transitions.md`](06_state_transitions.md).
- **Unit suite total**: **125** team tests (`DomainWhiteBoxTest`: 15, `AuthServiceWhiteBoxTest`: 11, `ExpenseServiceWhiteBoxTest`: 53, `ExpenseDtosValidationWhiteBoxTest`: 46); **157** total tests in CI with upstream integration tests.
  Evidence: [`docs/team/evidence/12_fix_pr_after_logs.zip`](evidence/12_fix_pr_after_logs.zip).

---

## 4. Mutation Analysis (PIT + Custom Mutators)

- **Score (`DEFAULTS` + 2 custom mutators)**: **74/82 (90%)** before fixes → **81/82 (99%)** after adding 4 assertion-strengthening tests; extended `ALL` + custom: **312/333 (94%)** → **328/333 (98%, 99% test strength)**.
- **Custom business-rule mutators** (`tools/pit-custom-mutators/`):
  1. `DROP_DEPARTMENT_CHECK` (BR2): drops manager department equality check in `assertCanDecide` (**1/1 killed**).
  2. `SWAP_APPROVER_ROLE` (BR3/BR4): swaps `Role.MANAGER` and `Role.FINANCE` in `RequestStatus.approverRole()` (**2/2 killed**).
- **Surviving mutants**: **21** survivors/no-coverage mutants were analysed in the extended run (`ALL` + custom): **16** were killed by new assertion-strengthening tests, and **5** remain equivalent/unreachable (1 in `DEFAULTS`: `setStatus(DRAFT)` redundant with field default; plus Hibernate lazy-touch `.size()` and `javac` `MatchException` switch defaults). See [`docs/team/04_mutation_testing.md`](04_mutation_testing.md) for the full survivor table.
  Evidence: [`docs/team/04_mutation_testing.md`](04_mutation_testing.md), [`docs/team/evidence/07_pit_defaults_custom_after_run.txt`](evidence/07_pit_defaults_custom_after_run.txt), [`docs/team/evidence/07_pit_all_custom_after_run.txt`](evidence/07_pit_all_custom_after_run.txt).

---

## 5. CI Quality Gate

Workflow [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) enforces:
- 100% JaCoCo check on the 4 scoped classes,
- Full suite (`157` tests),
- SonarQube `SQE-CI` gate (`bugs > 0`, `vulnerabilities > 2`, `code_smells > 0`, `coverage < 50%`, `duplication > 3%` — derived from measured baseline so upstream issues don't falsely block PRs while regressions fail),
- PIT mutation threshold **`95%`** (set below `99%` to allow the 1 equivalent mutant).

**Gate demonstrations** (Evidence: [`docs/team/09_blocked_and_fix_pr.md`](09_blocked_and_fix_pr.md)):
- **Blocked PR #3** (`demo/blocked-drop-department-check`, run [45770054227](https://github.com/Anfey-SE/expense-approval/actions/runs/45770054227)): failed at team-tests step (`Tests run: 120, Failures: 3`). Never merged.
- **Fix PR #5** (`fix/currency-validation`, Issue #4):
  - Commit 1 red (run [45794816172](https://github.com/Anfey-SE/expense-approval/actions/runs/45794816172)): `Tests run: 121, Failures: 1` (`currency_numeric123_isInvalid`).
  - Commit 2 green (run [45866994641](https://github.com/Anfey-SE/expense-approval/actions/runs/45866994641)): added `@Pattern(regexp = "[A-Za-z]{3}")` + 4 tests; **125** team tests, **157** full suite, Sonar `QUALITY GATE STATUS: PASSED`, PIT **81/82 (99%)**. Merged (`0dfa6ce`).

---

## 6. Use Cases UC1 & UC2 (Playwright E2E)

Automated in [`tests/team/e2e/`](../../tests/team/e2e/) (Chromium, `workers: 1`). Every test asserts both displayed UI and an independent postcondition (reload, API `GET`, or list check).
Evidence: [`docs/team/uc/UC1_submit_draft.md`](uc/UC1_submit_draft.md), [`docs/team/uc/UC2_create_draft.md`](uc/UC2_create_draft.md), [`docs/team/evidence/uc/run1.txt`](evidence/uc/run1.txt), [`docs/team/evidence/uc/run2.txt`](evidence/uc/run2.txt), [`docs/team/evidence/uc/mutation_check_currency.txt`](evidence/uc/mutation_check_currency.txt).

| UC | Flow | Test Name | Postcondition Assertion | Result |
|---|---|---|---|---|
| UC1 Submit | M | `UC1_M_submit_draft` | `uc1-submit.spec.ts` L25–29 (`page.reload()`, status + button gone + trail) | Passed (2/2 runs) |
| UC1 Submit | A1 | `UC1_A1_submit_three_items` | `uc1-submit.spec.ts` L58–62 (`page.reload()`, status + total + trail) | Passed (2/2 runs) |
| UC1 Submit | A2 | `UC1_A2_draft_not_submitted` | `uc1-submit.spec.ts` L78–82 (`page.reload()`, still `draft` + button visible) | Passed (2/2 runs) |
| UC1 Submit | E1 | `UC1_E1_button_gone_after_submit` | `uc1-submit.spec.ts` L103–106 (`page.reload()`, button count 0) | Passed (2/2 runs) |
| UC1 Submit | E2 | `UC1_E2_cross_user_access_denied` | `uc1-submit.spec.ts` L130–133 (`page.goto("/")`, absent from Carol's list) | Passed (2/2 runs) |
| UC2 Create | M | `UC2_M_create_draft_one_item` | `uc2-create.spec.ts` L31–41 (API `GET /api/requests/{id}`) | Passed (2/2 runs) |
| UC2 Create | A1 | `UC2_A1_add_remove_items` | `uc2-create.spec.ts` L76–84 (API `GET /api/requests/{id}`) | Passed (2/2 runs) |
| UC2 Create | A2 | `UC2_A2_remove_button_disabled` | `uc2-create.spec.ts` L105–108 (`page.goto("/")`, absent from list) | Passed (2/2 runs) |
| UC2 Create | E1 | `UC2_E1_blank_title` | `uc2-create.spec.ts` L128–131 (`page.goto("/")`, absent from list) | Passed (2/2 runs) |
| UC2 Create | E2 | `UC2_E2_invalid_currency` | `uc2-create.spec.ts` L153–156 (`page.goto("/")`, absent from list) | Passed (2/2 runs); failed when `@Pattern` removed |

---

## 7. Findings (Defects & Observations)

1. **Issue #4 (closed, Fixed in PR #5)**: `CreateRequest.currency` lacked `@Pattern(regexp = "[A-Za-z]{3}")`, accepting `"123"` ([`docs/team/issues/currency_validation.md`](issues/currency_validation.md)).
2. **Issue #8 (open, bug — Minor UX)**: `NewRequest.tsx` displays generic `"Request validation failed"` instead of field-level `"currency must be 3 letters"` ([`docs/team/issues/ui_generic_validation_error.md`](issues/ui_generic_validation_error.md)).
3. **Issue #9 (open, enhancement/observation)**: `PUT /api/requests/{id}` exists in `ExpenseController.java`, but no edit form exists in the React UI (covered by Member 2 at API level; [`docs/team/issues/ui_no_edit_form.md`](issues/ui_no_edit_form.md)).

---

## 8. Limitations

- Playwright E2E tests (`tests/team/e2e/`) are run locally against the live app (`:5173` / `:8081`) and are **not** yet wired into CI (`quality-gate`).
- Upstream integration tests (`src/test/`) require Docker (Testcontainers PostgreSQL 16).
- `ExpenseController.java` and security filters have `0.0%` coverage in team unit-only JaCoCo/Sonar runs (covered by upstream integration tests and Member 2's API tests).
