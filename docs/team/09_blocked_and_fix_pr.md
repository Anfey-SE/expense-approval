# Task 7 Evidence — Blocked PR & Fix PR

This document records the two required pull requests demonstrating the CI quality gate (`.github/workflows/ci.yml`):
1. **Blocked PR (#3)** — intentionally removes a business-rule guard; CI blocks it. Never merged.
2. **Fix PR (#5)** — demonstrates a real defect (`currency` accepting `"123"`) failing CI on Commit 1, then passing all gates on Commit 2 before merging into `master`.

All log lines below are copied verbatim from `0_quality-gate.txt` inside the archived GitHub Actions log zips in `docs/team/evidence/`, with only the leading UTC timestamps (`YYYY-MM-DDTHH:MM:SS.nnnnnnnZ `) removed.

---

## 1. Blocked PR — Drop Department Check (`PR #3`)

| Field | Value |
|-------|-------|
| Pull request | https://github.com/Anfey-SE/expense-approval/pull/3 |
| Branch | `demo/blocked-drop-department-check` (never merged) |
| Commit | `34b7179` (*Demo (blocked PR): drop department check in assertCanDecide*) |
| CI run URL | https://github.com/Anfey-SE/expense-approval/actions/runs/45770054227 |
| Failed step | Step 5: `Run team tests with JaCoCo report and 100 % check` |
| Evidence | `docs/team/evidence/10_blocked_pr_logs.zip`, `10_blocked_pr_page.png`, `10_blocked_pr_actions_list.png`, `10_blocked_pr_run_summary.png`, `10_blocked_pr_failed_step.png` |

Because the run stopped at `Run team tests with JaCoCo report and 100 % check`, the subsequent full test suite, SonarQube, and PIT steps did not run in that run (confirmed by `10_blocked_pr_logs.zip`, which contains only steps 1–5 plus the `always()` artifact upload step 11 and post/complete steps 21–23).

### Verbatim CI Log Excerpt (`10_blocked_pr_logs.zip` -> `0_quality-gate.txt`)

```text
[ERROR] Tests run: 53, Failures: 3, Errors: 0, Skipped: 0, Time elapsed: 1.396 s <<< FAILURE! -- in com.sandy.expense.service.ExpenseServiceWhiteBoxTest
[ERROR] com.sandy.expense.service.ExpenseServiceWhiteBoxTest.approve_managerPrincipalWithoutDepartment_isForbidden -- Time elapsed: 0.015 s <<< FAILURE!
[ERROR] com.sandy.expense.service.ExpenseServiceWhiteBoxTest.reject_managerOtherDepartment_isForbidden -- Time elapsed: 0.003 s <<< FAILURE!
[ERROR] com.sandy.expense.service.ExpenseServiceWhiteBoxTest.approve_managerOtherDepartment_isForbidden_D3_BtoTrue -- Time elapsed: 0.003 s <<< FAILURE!
[INFO] Tests run: 11, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.241 s -- in com.sandy.expense.service.AuthServiceWhiteBoxTest
[ERROR] Failures: 
[ERROR]   ExpenseServiceWhiteBoxTest.approve_managerOtherDepartment_isForbidden_D3_BtoTrue:461 
[ERROR]   ExpenseServiceWhiteBoxTest.approve_managerPrincipalWithoutDepartment_isForbidden:498 
[ERROR]   ExpenseServiceWhiteBoxTest.reject_managerOtherDepartment_isForbidden:561 
[ERROR] Tests run: 120, Failures: 3, Errors: 0, Skipped: 0
[INFO] BUILD FAILURE
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-surefire-plugin:3.5.6:test (default-test) on project expense-approval: There are test failures.
##[error]Process completed with exit code 1.
```

---

## 2. Fix PR — Currency Validation (`PR #5`, Issue `#4`)

| Field | Value |
|-------|-------|
| Pull request | https://github.com/Anfey-SE/expense-approval/pull/5 (merged into `master` at `0dfa6ce`) |
| PR title | `Fix: validate currency as 3 letters (closes #4)` |
| Issue referenced | `Fixes #4.` / `Closes #4` (write-up in `docs/team/issues/currency_validation.md`) |
| Branch | `fix/currency-validation` |

### 2.1 Before Fix — Failing Test Only (Commit 1: `7b96f70`)

| Field | Value |
|-------|-------|
| Commit | `7b96f70` (*Test (failing): reject non-alphabetic currency '123' in CreateRequest*) |
| CI run URL | https://github.com/Anfey-SE/expense-approval/actions/runs/45794816172 |
| Failed step | Step 5: `Run team tests with JaCoCo report and 100 % check` |
| Evidence | `docs/team/evidence/11_fix_pr_before_logs.zip`, `11_fix_pr_before_page.png`, `11_fix_pr_before_actions_list.png`, `11_fix_pr_before_run_summary.png`, `11_fix_pr_before_failed_step.png` |

#### Verbatim CI Log Excerpt (`11_fix_pr_before_logs.zip` -> `0_quality-gate.txt`)

```text
[INFO] Tests run: 15, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.402 s -- in com.sandy.expense.domain.DomainWhiteBoxTest
[ERROR] Tests run: 42, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.921 s <<< FAILURE! -- in com.sandy.expense.web.dto.ExpenseDtosValidationWhiteBoxTest
[ERROR] com.sandy.expense.web.dto.ExpenseDtosValidationWhiteBoxTest.currency_numeric123_isInvalid -- Time elapsed: 0.010 s <<< FAILURE!
[INFO] Tests run: 53, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 2.147 s -- in com.sandy.expense.service.ExpenseServiceWhiteBoxTest
[INFO] Tests run: 11, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.362 s -- in com.sandy.expense.service.AuthServiceWhiteBoxTest
[ERROR] Failures: 
[ERROR]   ExpenseDtosValidationWhiteBoxTest.currency_numeric123_isInvalid:146->assertInvalid:62 [expected a violation on 'currency'] 
[ERROR] Tests run: 121, Failures: 1, Errors: 0, Skipped: 0
[INFO] BUILD FAILURE
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-surefire-plugin:3.5.6:test (default-test) on project expense-approval: There are test failures.
##[error]Process completed with exit code 1.
```

### 2.2 After Fix — `@Pattern(regexp = "[A-Za-z]{3}")` + 4 New Tests (Commit 2: `2252ae8`)

| Field | Value |
|-------|-------|
| Commit | `2252ae8` (*Fix: enforce 3-letter A-Za-z pattern on CreateRequest.currency*) |
| Merge commit | `0dfa6ce` (*Merge pull request #5 from Anfey-SE/fix/currency-validation*) |
| CI run URL | https://github.com/Anfey-SE/expense-approval/actions/runs/45866994641 |
| CI status | `Success` (Total duration `2m 37s`, job `quality-gate` `2m 33s` per `12_fix_pr_after_run_summary.png`) |
| Evidence | `docs/team/evidence/12_fix_pr_after_logs.zip`, `12_fix_pr_after_page.png`, `12_fix_pr_after_actions_list.png`, `12_fix_pr_after_run_summary.png`, `12_fix_pr_after_passed_step.png` |

#### Verbatim CI Log Excerpts (`12_fix_pr_after_logs.zip` -> `0_quality-gate.txt`)

- **Step 5 (`Run team tests with JaCoCo report and 100 % check`)**:
```text
[INFO] Tests run: 15, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.322 s -- in com.sandy.expense.domain.DomainWhiteBoxTest
[INFO] Tests run: 46, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.621 s -- in com.sandy.expense.web.dto.ExpenseDtosValidationWhiteBoxTest
[INFO] Tests run: 53, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.462 s -- in com.sandy.expense.service.ExpenseServiceWhiteBoxTest
[INFO] Tests run: 11, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.282 s -- in com.sandy.expense.service.AuthServiceWhiteBoxTest
[INFO] Tests run: 125, Failures: 0, Errors: 0, Skipped: 0
[INFO] All coverage checks have been met.
[INFO] BUILD SUCCESS
```

- **Step 6 (`Run full test suite (upstream + team, JaCoCo skipped)`)** (also confirming `-Dapi.version=1.44` with Testcontainers on `ubuntu-latest`):
```text
[INFO] Tests run: 157, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

- **Step 9 (`Run SonarQube scan and enforce quality gate`)**:
```text
[INFO] ------------- Check Quality Gate status
[INFO] Waiting for the analysis report to be processed (max 300s)
[INFO] QUALITY GATE STATUS: PASSED - View details on http://localhost:9000/dashboard?id=com.sandy%3Aexpense-approval
[INFO] BUILD SUCCESS
```

- **Step 10 (`Run PIT mutation testing (threshold 95 %)`)**:
```text
>> Generated 82 mutations Killed 81 (99%)
[INFO] BUILD SUCCESS
```
