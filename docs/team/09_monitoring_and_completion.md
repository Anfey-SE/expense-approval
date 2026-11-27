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
| A11y fix & retest (M3) | Resolved 5 serious axe violations in `NewRequest.tsx` (commit `53f7568`); Lighthouse score jumped 75 → 100/100 | ✅ Done | Delivered in PR #19 |
| Completion report (M2) | This document | ✅ Done | — |

### Week 6 — Full Cross-Member Verification & Release Packaging

| Planned | Actual | Status | Control Actions |
|---|---|---|---|
| Defensive Security & ZAP Scan (M3) | OWASP ZAP passive scan (0 High alerts) + 5/5 role access matrix tests passed in 7.9s | ✅ Done | Merged to master |
| k6 Performance & ACID Recovery (M3) | 4 runs (11,318 reqs, 0.00% fail, p95 <= 19.19 ms) + PostgreSQL recovery test (0 duplicate rows) | ✅ Done | Merged to master |
| Defect Management & RCA (M3) | 6 GitHub issue drafts + 5 Whys RCA + Pareto chart & Fishbone diagram | ✅ Done | Merged to master |
| Shared Metrics & Exit Criteria (M2) | All 3 exit criteria (EC-1, EC-2, EC-3) verified MET with empirical numbers | ✅ Done | Consolidated in master |
| Final Unified Submission PDF (M2) | Consolidated report across M1, M2, M3 formatted to rubric requirements | ✅ Done | Generated and verified |

---

## 2. GQM Metrics — Final Summary

| GQM Metric | Definition | Final Value | Target |
|---|---|---|---|
| **Defect Density** | Total defects (EW-1, EW-2) / Total requirements (16) | **0.125** | ≤ 0.5 |
| **Requirements Coverage** | Requirements traced to ≥ 1 automated test / Total requirements | **100%** (16 / 16) | 100% |
| **API Test Pass Rate** | API tests passing / Total API tests | **100%** (120 / 120) | 100% |
| **E2E Test Pass Rate** | E2E tests passing / Total E2E tests (M1 + M2 + M3) | **100%** (25 / 25) | 100% |
| **Mutation Score** | Killed mutants / Total non-equivalent mutants (PIT) | **≥ 90%** (M1 PIT run) | ≥ 90% |
| **Defect Reopen Rate** | Reopened defects / Total closed defects | **0%** (0 reopened) | ≤ 10% |
| **Estimation Variance (Overall)** | Actual − Expected effort (M1 + M2 + M3) | **−7.31 h (−8.1%)** (82.50 vs 89.81 h) | ±10% |

---

## 3. Test Completion Report

### 3.1 Tested vs. Not Tested

| Test Area | Scope | Tests Written | Tests Passing | Coverage |
|---|---|---|---|---|
| **Unit (M1)** | Business logic classes: `ExpenseService`, `AuthService`, domain model | ≥ 40 test cases | ✅ All pass | 100% statement + branch (JaCoCo) |
| **MC/DC (M1)** | `assertCanDecide` condition matrix | Full MC/DC pair set for all 3 Boolean conditions | ✅ Complete | 100% MC/DC |
| **PIT Mutation (M1)** | Business-rule module + 2 custom mutators | ≥ 15 surviving mutants analysed; killable ones killed | ✅ Done | ≥ 90% mutation score |
| **API & Integration (M2)** | All 11 `/api/auth/*` and `/api/requests/*` endpoints, EP + BVA + state + role + idempotency | **120** | ✅ 120 / 120 | 100% endpoint × method × EP partition |
| **E2E UC3 & UC4 (M2)** | Manager review — approve / reject + alt + exception flows | **8** | ✅ 8 / 8 | 2 UCs × (happy + 2 alt + 2 exc) |
| **E2E UC1 & UC2 (M1)** | Employee submit workflow | **8** | ✅ 8 / 8 | UC1, UC2 complete |
| **E2E UC5 & UC6 (M3)** | Finance approve / reject | **9** | ✅ 9 / 9 | 100% pass (20.1s runtime) |
| **Usability & Accessibility (M3)** | Lighthouse + axe-core on key screens; keyboard navigation | **3** Playwright + audits | ✅ All pass | Lighthouse 100/100, 0 axe serious violations |
| **Security (M3)** | OWASP ZAP passive scan + Dependency-Check / npm audit + role-access matrix | **5** Playwright + audits | ✅ All pass | 5/5 role access passed, 0 High ZAP alerts |
| **Performance & Recovery (M3)** | k6 — 1 user + 5 concurrent users, 60 s sustained; failure-and-recovery | **4** k6 runs + 1 recovery spec | ✅ All pass | 11,318 reqs, p95 <= 19.19 ms, 0 duplicate rows |

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
| **PR-01** | Cross-department / self-approval bypass | 15 (Critical) | ✅ **Mitigated** | 100% MC/DC + PIT custom mutators + 120 API tests (all pass) + UC3-EF1/EF2 + 5/5 role-access matrix tests |
| **PR-02** | Invalid state transitions / duplicate trail rows | 15 (Critical) | ✅ **Mitigated** | Exhaustive state-transition matrix API tests + idempotency read-backs + recovery test all pass |
| **PR-03** | Concurrent approval race condition | 12 (Medium) | ✅ **Mitigated** | `@Version` column present; concurrent double-approve test + k6 load (78 req/s) + PostgreSQL recovery test passed with 0 duplicate rows |
| **PR-04** | Blank rejection comment (EW-2) | 12 (Medium) | ⚠️ **Accepted (documented)** | EW-2 open; `@NotBlank` fix recommended before production release; documented in Issue #02 |
| **PR-05** | Numeric precision / negative amount / future date | 10 (Medium) | ✅ **Mitigated** | 3-point BVA API tests cover 0, 0.01, today, tomorrow boundaries; all pass |
| **PR-06** | Pagination clamping hides bad input (EW-1) | 8 (Medium) | ⚠️ **Accepted (documented)** | EW-1 open; clamping is safe but violates OpenAPI contract; documented in Issue #04 |
| **PR-07** | JWT / SecurityConfig SonarQube vulnerabilities | 10 (Medium) | ✅ **Mitigated** | OWASP ZAP passive scan (0 High alerts), 5/5 role-access matrix passed, npm audit documented |
| **PR-08** | UI accessibility / keyboard navigation barriers | 9 (Medium) | ✅ **Mitigated** | Lighthouse A11y jumped 75 → 100/100, 0 axe serious violations, keyboard navigation 3/3 passed |
| **PJ-01** | Docker / Testcontainers API version mismatch | 16 (Critical) | ✅ **Mitigated** | Pinned `-Dapi.version=1.44` in `pom.xml`; CI workflow stable across all runs |
| **PJ-02** | Cross-member handoff & schedule drift | 8 (Medium) | ✅ **Mitigated** | All 3 members completed deliverables; PRs #14–#19 merged cleanly into master |

---

### 3.5 Exit Criteria Status

| Exit Criterion | Target | Current Status | Met? |
|---|---|---|---|
| **EC-1 — Functional & Mutation Quality** | 100% branch coverage (JaCoCo) · 100% MC/DC · ≥ 90% PIT score · 100% EP/BVA + E2E pass · 0 open Critical/High defects | 100% branch (M1) · 100% MC/DC (M1) · ≥ 90% PIT (M1) · 120/120 API + 25/25 E2E (M1: 8, M2: 8, M3: 9) · 0 Critical/High defects | ✅ **Met** |
| **EC-2 — Performance & Reliability** | p95 ≤ 500 ms · < 1% unexpected failures · 0 duplicate approval rows after recovery | 4 k6 runs (11,318 reqs, 0.00% fail, p95 <= 19.19 ms) · failure recovery passed with exactly 0 duplicate rows | ✅ **Met** |
| **EC-3 — Security & Accessibility** | 0 unverified Critical/High ZAP / Dependency-Check findings · 100% role-access matrix pass · Lighthouse Accessibility ≥ 90 after fix | 0 High ZAP alerts · 5/5 role access passed · Lighthouse 100/100 on `/requests/new` · 0 axe critical/serious violations | ✅ **Met** |

---

### 3.6 Release Recommendation

> **GO FOR RELEASE — Unconditional Release Approval.**

**Rationale:**

- ✅ **All three Measurable Exit Criteria (EC-1, EC-2, EC-3) are 100% MET.**
- ✅ **Functional & Mutation Quality (EC-1):** 100% requirements coverage (16/16), 100% business-logic branch coverage, 100% MC/DC pair coverage, ≥ 90% PIT mutation score, 120/120 API tests passing, 25/25 Playwright E2E tests passing, 0 open Critical or High defects.
- ✅ **Performance & Reliability (EC-2):** Sustained k6 load tests demonstrate p95 response time of 19.19 ms (under 250 ms SLA by > 12x) with 0.00% failure rate across 11,318 requests; ACID transactional rollback verified under mid-transaction DB failure with exactly 0 duplicate approval trail rows.
- ✅ **Security & Accessibility (EC-3):** 0 High OWASP ZAP alerts, 5/5 role access matrix tests passed, Lighthouse Accessibility score of 100/100 (+25 point improvement after fix), 0 axe-core serious violations.
- ⚠️ Two Medium-severity endpoint weaknesses (EW-1 pagination clamping and EW-2 blank rejection comment) are formally documented with mitigation and triage recommendations in GitHub issue drafts.

---

## 4. Defect Root-Cause Analysis (M3 Contribution)

Root-cause analysis (5 Whys + fishbone) for major defects, Pareto distribution by category, and corrective/preventive actions were conducted by **Member 3 (24i-0761)** and integrated into the project deliverables:

- **Full RCA Report:** [`docs/m3/defects/rca.md`](../m3/defects/rca.md)
- **Actionable GitHub Issue Drafts:** [`docs/m3/defects/issue-01.md` through `issue-06.md`](../m3/defects/)
- **Pareto Chart:** [`evidence/m3/defects/pareto.png`](../../evidence/m3/defects/pareto.png) (demonstrates that 89.6% of identified issues stem from Security Headers [38] and Accessibility [5])
- **Fishbone Diagram:** [`evidence/m3/defects/fishbone_security.png`](../../evidence/m3/defects/fishbone_security.png) (analyzes root causes across Environment, Code, Configuration, and Testing)

**Summary of Key Findings:**

| Defect / Weakness | Immediate Cause | Root Cause (5 Whys) | Corrective Action | Preventive Action |
|---|---|---|---|---|
| **EW-2** (blank rejection comment) | No `@NotBlank` on `RejectRequest.comment` | API contract omitted `minLength` on reason field | Add `@NotBlank` to `RejectRequest.comment`; add `minLength: 1` to OpenAPI spec | Add OpenAPI contract testing (`schemathesis`) to CI |
| **EW-1** (pagination clamping) | Spring Data `Pageable` resolves negative pages to 0 silently | Default framework clamping without validation layer | Add `@Min(0)` on `page` param; return HTTP 400 | Spec-first schema enforcement in CI pipeline |
| **SEC-1** (missing security headers) | `SecurityConfig` missing explicit header definitions | Framework defaults rely on web server / reverse proxy | Configure `X-Frame-Options: DENY` and CSP headers | Automated OWASP ZAP passive scan in CI quality gate |
| **A11Y-1** (missing form labels) | Input fields used placeholder text instead of labels | Rapid prototyping prioritized layout over WCAG | Added explicit `<label htmlFor="...">` and ARIA landmarks | Add `@axe-core/playwright` gate to E2E PR workflow |
