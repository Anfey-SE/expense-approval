# Weekly Monitoring Report & Test Completion Report

**Project:** Expense Approval MIS (`https://github.com/Anfey-SE/expense-approval`, baseline `ae596c3`)  
**Prepared by:** Member 2 (24i-3097) — Shared Test Management Lead  
**Group:** 24i-3112 (M1) · 24i-3097 (M2) · 24i-0761 (M3)  
**Report Date:** 2026-11-26

---

## 1. Weekly Progress Reports vs. Plan

### Week 1 — Scope & Environment Setup

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| Repo confirmed, local run, Google Sheet registration | Repo forked (`Anfey-SE/expense-approval`), baseline commit `ae596c3` saved, all 5 synthetic accounts seeded via `DataSeeder.java` | ✅ Done | None required |
| Identify 8 functional requirements, 4 business rules, 2 user roles | 16 requirements (`REQ-A1..A4`, `REQ-E1..E8`, `REQ-AP1..AP4`), 4 business rules (`BR1..BR4`), 2 roles (`EMPLOYEE`, `MANAGER`+`FINANCE`) documented in `01_system_and_scope.md` | ✅ Done | Expanded to 16 reqs — no schedule impact |

**GQM Metrics — Week 1:**

| Metric | Formula | Value |
|---|---|---|
| Requirements Coverage | Reqs traced / Total reqs | 16 / 16 = **100%** |
| Defects Opened | New issues filed | 0 |
| Defect Density | Defects / Requirement | 0.00 |

---

### Week 2 — Test Planning, OpenAPI Spec, Static Analysis

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| Test plan + risk register (M2) | `07_test_plan_and_estimation.md`, `08_risk_register_and_exit_criteria.md` created; 10 risks (8 product + 2 project) on 5×5 matrix | ✅ Done | — |
| OpenAPI spec draft (M2) | `tests/team/api/openapi.yaml` — covers all 11 endpoint paths with constraints | ✅ Done | — |
| SonarQube + CI skeleton (M1) | `docs/team/02_static_analysis.md` committed; CI workflow `.github/workflows/ci.yml` active | ✅ Done | — |
| Docker Compose setup | Port conflict (8081 occupied) → used `--server.port=8085`; Docker build blocked by local-only `pit-custom-mutators` → ran Spring Boot via `mvnw` directly | ✅ Done | Documented workaround in `01_system_and_scope.md` |

**GQM Metrics — Week 2:**

| Metric | Value |
|---|---|
| Requirements Coverage | 100% |
| Defects Opened (endpoint weaknesses) | 2 (EW-1, EW-2 — Medium severity) |
| Defect Density | 2 / 16 = **0.125 per requirement** |
| Reopen Rate | 0 / 2 = **0%** |

---

### Week 3 — EP/BVA Generator, API Tests, Unit Tests, MC/DC

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| Generator reads OpenAPI spec → EP classes + BVA triples (M2) | `generate_test_data.py` produces **162 EP cases + 95 BVA cases = 257 total** | ✅ Done | — |
| API & integration pytest suite using generator output (M2) | `test_expense_api.py`: **97 tests, 97 passed** | ✅ Done | — |
| White-box unit tests 100% branch + MC/DC (M1) | `ExpenseServiceWhiteBoxTest`, `DomainWhiteBoxTest`, `AuthServiceWhiteBoxTest`; JaCoCo 100% branch on business-logic classes | ✅ Done | — |
| PIT mutation + custom mutators (M1) | Custom mutators installed to local Maven repo; PIT score ≥ 90% | ✅ Done | Mutators built from `tools/pit-custom-mutators/` before `spring-boot:run` |

**GQM Metrics — Week 3:**

| Metric | Value |
|---|---|
| Requirements Coverage | 100% (16 / 16, RTM complete) |
| API Test Pass Rate | 97 / 97 = **100%** |
| Defects Closed | 0 (EW-1, EW-2 documented as weaknesses; no fix landed yet) |
| Reopen Rate | 0% |

---

### Week 4 — E2E Use Cases, Regeneration Demo

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| UC3 & UC4 Playwright automation (M2) | `test_uc3_uc4_manager_review.py`: **8 tests, 8 passed** (happy, alternative, exception flows) | ✅ Done | Fixed "Sign out" → "Log out" label; fixed state-transition test expecting 403 on second approve |
| Regeneration demo — change 2 constraints (M2) | `title.maxLength` 200→100 and `items.maxItems` 100→50; BVA values updated; demo recorded in `docs/team/evidence/regeneration_demo.txt` | ✅ Done | — |
| Use case specs UC3, UC4 (M2) | `docs/team/06_use_cases_member2.md` — 2 alternative + 2 exception flows each | ✅ Done | — |
| UC1 & UC2 E2E (M1) | Covered by M1 Playwright suite | ✅ Done | — |
| Usability, Security, Performance (M3) | In progress (Lighthouse, axe-core, OWASP ZAP, k6) | 🔄 In Progress | M3 to integrate before final submission |

**GQM Metrics — Week 4:**

| Metric | Value |
|---|---|
| E2E Test Pass Rate (M1 + M2 UCs) | 8 M2 tests + M1 UCs = all passing |
| Total Automated Tests Passing | **105** (97 API + 8 E2E) |
| Open Defects (EW-1, EW-2) | 2 — Medium severity, documented |
| Requirements Coverage | 100% |
| Reopen Rate | 0% |

---

### Week 5 — CI Gate, Final Integration

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| Mutation + CI quality gate (M1) | GitHub Actions blocks merge on SonarQube / coverage / mutation failures; documented blocked PR and passing PR | ✅ Done | — |
| OpenAPI regeneration demo in CI | Spec changeset committed; `generate_test_data.py` re-run shows updated BVA output | ✅ Done | — |
| A11y fix & retest (M3) | In progress | 🔄 In Progress | M3 to deliver before submission |
| Completion report (M2) | This document | ✅ Done | — |

---

## 2. GQM Metrics — Final Summary

| GQM Metric | Definition | Final Value | Target |
|---|---|---|---|
| **Defect Density** | Total defects (EW-1, EW-2) / Total requirements (16) | **0.125** | ≤ 0.5 |
| **Requirements Coverage** | Requirements traced to ≥ 1 automated test / Total requirements | **100%** (16 / 16) | 100% |
| **API Test Pass Rate** | API tests passing / Total API tests | **100%** (97 / 97) | 100% |
| **E2E Test Pass Rate** | E2E tests passing / Total E2E tests (M2 scope) | **100%** (8 / 8) | 100% |
| **Mutation Score** | Killed mutants / Total non-equivalent mutants (PIT) | **≥ 90%** (M1 PIT run) | ≥ 90% |
| **Defect Reopen Rate** | Reopened defects / Total closed defects | **0%** (0 closed yet) | ≤ 10% |
| **Estimation Variance (M1 + M2)** | Actual − Expected effort | **+0.52 h** (67.50 vs 66.98 h) | ±10% |

---

## 3. Test Completion Report

### 3.1 Tested vs. Not Tested

| Test Area | Scope | Tests Written | Tests Passing | Coverage |
|---|---|---|---|---|
| **Unit (M1)** | Business logic classes: `ExpenseService`, `AuthService`, domain model | ≥ 40 test cases | ✅ All pass | 100% statement + branch (JaCoCo) |
| **MC/DC (M1)** | `assertCanDecide` condition matrix | Full MC/DC pair set for all 3 Boolean conditions | ✅ Complete | 100% MC/DC |
| **PIT Mutation (M1)** | Business-rule module + 2 custom mutators | ≥ 15 surviving mutants analysed; killable ones killed | ✅ Done | ≥ 90% mutation score |
| **API & Integration (M2)** | All 11 `/api/auth/*` and `/api/requests/*` endpoints, EP + BVA + state + role + idempotency | **97** | ✅ 97 / 97 | 100% endpoint × method × EP partition |
| **E2E UC3 & UC4 (M2)** | Manager review — approve / reject + alt + exception flows | **8** | ✅ 8 / 8 | 2 UCs × (happy + 2 alt + 2 exc) |
| **E2E UC1 & UC2 (M1)** | Employee submit workflow | M1 scope | ✅ Per M1 report | UC1, UC2 complete |
| **E2E UC5 & UC6 (M3)** | Finance approve / reject | M3 scope | 🔄 In progress | Pending M3 delivery |
| **Usability & Accessibility (M3)** | Lighthouse + axe-core on key screens; keyboard navigation | M3 scope | 🔄 In progress | Pending M3 delivery |
| **Security (M3)** | OWASP ZAP passive scan + Dependency-Check / npm audit + role-access matrix | M3 scope | 🔄 In progress | Pending M3 delivery |
| **Performance & Recovery (M3)** | k6 — 1 user + 5 concurrent users, 60 s sustained; failure-and-recovery | M3 scope | 🔄 In progress | Pending M3 delivery |

---

### 3.2 Deviations from Plan

| Deviation | Root Cause | Impact | Resolution |
|---|---|---|---|
| Spring Boot started on port 8085 (planned 8081) | Port 8081 occupied by another process on dev machine | Low — test suite uses `EXPENSE_BASE_URL` env var | Added `--server.port=8085`; env var updated |
| Docker Compose build fails (`pit-custom-mutators` not in public registry) | Local-only Maven artefact not pushed to any registry | Low — CI uses separate `mvnw` steps | Documented workaround; `mvnw` runs directly |
| Blank rejection comment accepted (EW-2) | No `@NotBlank` on `RejectRequest.comment` DTO | Medium — employees lack actionable feedback | Documented as EW-2; recommended `@NotBlank` fix |
| Pagination clamping returns HTTP 200 on `page=-1` (EW-1) | Spring Data silently clamps negative page to 0 | Medium — API contract violation | Documented as EW-1; logged as known issue |

---

### 3.3 Open Defects

| ID | Severity | Priority | Status | Description | Triage Decision |
|---|---|---|---|---|---|
| **EW-1** | Medium | P3 | Open | `GET /api/requests?page=-1&size=0` returns HTTP 200 (clamped) instead of HTTP 400 | Accept for now — clamping is safe; fix in next sprint |
| **EW-2** | Medium | P2 | Open | `POST /api/requests/{id}/reject` accepts blank/null comment, leaving employees without actionable feedback | Recommend `@NotBlank` on DTO; patch before production |

> **No Critical or High open defects.** Both open defects are Medium severity.

---

### 3.4 Residual Risk Assessment

| Risk ID | Description | Score | Residual Status | Evidence |
|---|---|---|---|---|
| **PR-01** | Cross-department / self-approval bypass | 15 (Critical) | ✅ **Mitigated** | 100% MC/DC + PIT custom mutators + 97 API tests (all pass) + UC3-EF1/EF2 Playwright tests |
| **PR-02** | Invalid state transitions / duplicate trail rows | 15 (Critical) | ✅ **Mitigated** | Exhaustive state-transition matrix API tests + idempotency read-backs all pass |
| **PR-03** | Concurrent approval race condition | 12 (Medium) | 🔄 **Partially mitigated** | `@Version` column present in source; M3 recovery test to confirm runtime behaviour |
| **PR-04** | Blank rejection comment (EW-2) | 12 (Medium) | ⚠️ **Accepted (documented)** | EW-2 open; `@NotBlank` fix recommended before production release |
| **PR-05** | Numeric precision / negative amount / future date | 10 (Medium) | ✅ **Mitigated** | 3-point BVA API tests cover 0, 0.01, today, tomorrow boundaries; all pass |
| **PR-06** | Pagination clamping hides bad input (EW-1) | 8 (Medium) | ⚠️ **Accepted (documented)** | EW-1 open; clamping is safe but violates OpenAPI contract |
| **PR-07** | JWT / SecurityConfig SonarQube vulnerabilities | 10 (Medium) | 🔄 **Partially mitigated** | SonarQube Rating D flagged (M1); M3 OWASP ZAP passive scan pending |
| **PR-08** | UI accessibility / keyboard navigation barriers | 9 (Medium) | 🔄 **Partially mitigated** | M3 Lighthouse + axe-core pending; UC3 keyboard navigation tested in `test_uc3_keyboard_navigation_and_form_submission` |
| **PJ-01** | Docker / Testcontainers API version mismatch | 16 (Critical) | ✅ **Mitigated** | Pinned `-Dapi.version=1.44` in `pom.xml`; CI workflow stable |
| **PJ-02** | Cross-member handoff & schedule drift | 8 (Medium) | ✅ **Mitigated** | M1 and M2 deliverables committed on schedule; M3 in progress |

---

### 3.5 Exit Criteria Status

| Exit Criterion | Target | Current Status | Met? |
|---|---|---|---|
| **EC-1 — Functional & Mutation Quality** | 100% branch coverage (JaCoCo) · 100% MC/DC · ≥ 90% PIT score · 100% EP/BVA + E2E pass · 0 open Critical/High defects | 100% branch (M1) · 100% MC/DC (M1) · ≥ 90% PIT (M1) · 97/97 API + 8/8 E2E (M2) · 0 Critical/High defects | ✅ **Met** (M1 + M2 scope) |
| **EC-2 — Performance & Reliability** | p95 ≤ 500 ms · < 1% unexpected failures · 0 duplicate approval rows after recovery | 0 duplicate rows confirmed (API idempotency tests) · k6 results pending (M3) | 🔄 **Partially met** — awaiting M3 k6 run |
| **EC-3 — Security & Accessibility** | 0 unverified Critical/High ZAP / Dependency-Check findings · 100% role-access matrix pass · Lighthouse Accessibility ≥ 90 after fix | Role-access verified in API tests; ZAP + Lighthouse pending (M3) | 🔄 **Partially met** — awaiting M3 delivery |

---

### 3.6 Release Recommendation

> **CONDITIONAL HOLD — recommend release only after M3 delivers EC-2 and EC-3 evidence.**

**Rationale:**

- ✅ All M1 + M2 quality gates pass: 100% requirements coverage, 97/97 API tests, 8/8 E2E tests, 0 Critical/High defects, ≥ 90% mutation score, CI blocks merge on failures.
- ⚠️ Two Medium-severity endpoint weaknesses (EW-1, EW-2) are accepted with mitigations documented.
- 🔄 EC-2 (k6 performance) and EC-3 (ZAP + Lighthouse) evidence is pending M3 delivery.
- 🔄 Once M3 commits results and all three exit criteria are verified, upgrade to **RELEASE**.

---

## 4. Defect Root-Cause Analysis (M3 Responsibility)

> Root-cause analysis (5 Whys + fishbone) for at least 2 major defects, Pareto by category, and corrective/preventive actions are owned by **Member 3 (24i-0761)** per the work-division agreement and will be added to this document or a separate `10_defect_rca.md` file by M3 before final submission.

**Preview of EW-1 and EW-2 for M3 input:**

| Defect | Immediate Cause | Corrective Action | Preventive Action |
|---|---|---|---|
| **EW-2** (blank rejection comment) | No `@NotBlank` on `RejectRequest.comment`; API contract omits `minLength` on `reason` field | Add `@NotBlank` to `RejectRequest.comment`; add `minLength: 1` to OpenAPI spec | Add OpenAPI spec validation checks to CI: schema-first development with spec-first DTO generation |
| **EW-1** (pagination clamping) | Spring Data `Pageable` resolves negative pages to 0 silently; no custom validator added | Add `@Min(0)` constraint on `page` parameter + return HTTP 400 on violation | Add OpenAPI spec contract tests (e.g., `schemathesis`) to CI to catch silent clamping |
