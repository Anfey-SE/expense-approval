# Risk Register and Measurable Exit Criteria

**Project:** Expense Approval MIS  
**Prepared by:** Member 2 (24i-3097) — Shared Test Management Lead

---

## 1. Risk Register (5 × 5 Matrix: Likelihood 1–5 × Impact 1–5)

### 1.1 Product Risks (8)
| ID | Risk Description | Likelihood (L) | Impact (I) | Score (L×I) | Tier | Linked Test Technique & Depth | Mitigation / Control |
|---|---|---|---|---|---|---|---|
| **PR-01** | **Cross-department or self-approval bypass (BR2/BR4):** A manager approves a request from another department or approves their own request, or Finance approves before Manager. | 3 | 5 | **15** | Critical | White-box MC/DC on `assertCanDecide` + PIT custom mutators + API role-matrix tests + Playwright UC3-EF1/EF2 | Verify 403/404 at both `@PreAuthorize` and `ExpenseService` layers. |
| **PR-02** | **Invalid state transitions & duplicate trail rows (BR3):** Submitting non-DRAFT, approving TERMINAL states, or double-clicking creates duplicate `Approval` rows. | 3 | 5 | **15** | Critical | White-box state-transition unit tests + API full state-transition matrix & repeated-request idempotency read-backs | Assert HTTP 409 and exact `approvals.length` after every rejection. |
| **PR-03** | **Concurrent approval race condition (REQ-E8):** Two approvers act simultaneously on the same request without optimistic locking. | 3 | 4 | **12** | Medium | Unit mock test for `ObjectOptimisticLockingFailureException` + M3 recovery/concurrency test | Verify `@Version` column triggers HTTP 409 `CONCURRENT_UPDATE`. |
| **PR-04** | **Blank rejection comment accepted (EW-2):** `POST /api/requests/{id}/reject` allows empty/omitted reason, leaving employees without actionable feedback. | 4 | 3 | **12** | Medium | API `test_reject_without_comment_weakness` + Playwright UC4-EF1 | Document as endpoint weakness EW-2; recommend `@NotBlank` on reject DTO. |
| **PR-05** | **Numeric precision / negative amount / future date bypass (REQ-E2, REQ-E3):** Rounding mismatch or invalid line-item input causes 500 or wrong total. | 2 | 5 | **10** | Medium | OpenAPI-driven 3-point BVA (`amount` 0/0.01/10.123, `incurredOn` today/tomorrow) + `toItem()` rounding unit test | Enforce `@Positive`, `@Digits(10,2)`, `@PastOrPresent` and `HALF_UP`. |
| **PR-06** | **Pagination parameter clamping silently hides bad input (EW-1):** `GET /api/requests?page=-1&size=999` returns 200 instead of 400. | 4 | 2 | **8** | Medium | API `test_list_pagination_clamping_weakness` | Document as EW-1; verify clamping bounds `[0..100]`. |
| **PR-07** | **JWT / SecurityConfig exposure:** Upstream `SecurityConfig.java` flagged with 2 SonarQube vulnerabilities (Rating D). | 2 | 5 | **10** | Medium | SonarQube scan + M3 OWASP ZAP passive scan + Dependency-Check / `npm audit` | Review controls in security assessment and verify 401 on unauthenticated calls. |
| **PR-08** | **UI accessibility & keyboard navigation barriers:** Missing form labels, low contrast, or unreachable submit button in React UI. | 3 | 3 | **9** | Medium | M3 Lighthouse + `@axe-core/playwright` + keyboard navigation test + before/after fix | Fix critical a11y issues on key screen and verify score improvement. |

### 1.2 Project Risks (2)
| ID | Risk Description | Likelihood (L) | Impact (I) | Score (L×I) | Tier | Linked Mitigation |
|---|---|---|---|---|---|---|
| **PJ-01** | **Docker / Testcontainers API version mismatch:** Docker 29+ breaks older Testcontainers `api.version` during Maven integration tests. | 4 | 4 | **16** | Critical | Pinned `-Dapi.version=1.44` in `pom.xml` surefire config and documented in `01_system_and_scope.md` & CI workflow. |
| **PJ-02** | **Cross-member handoff & schedule drift:** Delay in baseline/CI or OpenAPI spec blocks downstream API, E2E, and security runs. | 2 | 4 | **8** | Medium | Weekly progress tracking (GQM metrics) by M2; early baseline commit and CI skeleton by M1. |

---

## 2. Measurable Exit Criteria

| Exit ID | Category | Measurable Target | Linked Highest Risk(s) | Actual Verified Result | Status |
|---|---|---|---|---|---|
| **EC-1** | **Functional & Mutation Quality** | **100%** statement & branch coverage on scoped server-side business logic (`JaCoCo`), **100%** MC/DC pair coverage on `assertCanDecide`, **>= 90%** PIT mutation score (with custom BR2/BR3/BR4 mutators), **100%** pass rate on generated EP/BVA API tests and UC1–UC6 Playwright flows, and **0** open Critical/High defects. | **PR-01** (15), **PR-02** (15) | **100%** statement & branch (JaCoCo), **100%** MC/DC, **≥90%** PIT mutation score, **120/120** API tests pass, **25/25** Playwright E2E tests pass (UC1–UC6: M1 8/8, M2 8/8, M3 9/9), **0** Critical/High open defects. | ✅ **MET** |
| **EC-2** | **Performance & Reliability** | Under k6 load (1 user and 5+ concurrent users, 60s+ sustained), **p95 <= 500 ms** and **< 1%** unexpected request failures; failure-and-recovery test leaves **0** duplicate approval trail rows. | **PR-02** (15), **PR-03** (12), **PJ-01** (16) | k6 4 runs (11,318 requests, 0.00% failures): 1 VU $p95 = 13.12–16.78\text{ ms}$, 5 VU $p95 = 18.60–19.19\text{ ms}$ (vs $\le 250\text{ ms}$ SLA); recovery test verified **exactly 0 duplicate approval trail rows** (`approvals.length === 2`). | ✅ **MET** |
| **EC-3** | **Security & Accessibility** | **0** unverified Critical/High security findings in OWASP ZAP passive scan / Dependency-Check / `npm audit`, **100%** pass on Playwright role-access matrix checks, and Lighthouse Accessibility score **>= 90** after UI fix with **0** critical `axe-core` violations. | **PR-01** (15), **PR-07** (10), **PR-08** (9) | **0** High ZAP alerts (12 Med, 26 Low, 20 Info); **5/5** role access tests passed; Lighthouse Accessibility on `/requests/new` jumped **75 → 100/100**; **0** critical/serious axe-core violations on fixed screen; 3/3 keyboard nav passed. | ✅ **MET** |
