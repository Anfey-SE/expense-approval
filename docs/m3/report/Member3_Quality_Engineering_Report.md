# Member 3 (24i-0761) — Quality Engineering Report Section

**Student:** Member 3 (roll no. 24i-0761, Section C)  
**Assigned Focus Area:** Usability, Accessibility, Defensive Security, Performance, Failure Recovery, UC5/UC6, Defect Management & RCA  
**Branch:** `member3/usability-security-performance-uc5-uc6`  

---

## 1. System & Scope Alignment

Member 3 owns end-to-end user journeys for **Workflow 1 (Submission)** and **Workflow 2 (Review & Final Approval)**, specifically Use Case 5 (Finance Approval) and Use Case 6 (Finance Rejection), alongside non-functional verification (WCAG 2.1 AA accessibility, OWASP ZAP defensive security, k6 performance load, ACID failure recovery, and root cause analysis).

---

## 2. Deliverable A: UC5 and UC6 Specification and E2E Automation

### 2.1 Specification Highlights (`docs/m3/use-cases.md`)
- **UC5: Finance Approves Manager-Approved Request**
  - Actor: Finance User (`fiona@acme.com`).
  - Preconditions: Request status is `MANAGER_APPROVED`.
  - Main Flow (MF): Fiona reviews line items, optionally enters comment, clicks "Approve", status transitions to `FINANCE_APPROVED`, immutable audit row appended.
  - Alternative Flows (AF1/AF2): Approval with long comment (500 chars); approval with blank comment.
  - Exception Flows (EF1/EF2): Premature approval attempt on `SUBMITTED` request (blocked); non-finance user attempt (HTTP 403).
- **UC6: Finance Rejects Manager-Approved Request**
  - Actor: Finance User (`fiona@acme.com`).
  - Main Flow (MF): Fiona rejects request, status transitions to terminal `REJECTED`, audit row appended.
  - Alternative Flows: Rejection with detailed policy explanation; rejection without comment.
  - Exception Flows: Double rejection / terminal state modification (HTTP 409 `INVALID_STATE`); unauthorized employee rejection (HTTP 403).

### 2.2 Automation Results (`tests/team/e2e/tests/uc5-uc6-finance.spec.ts`)
- Implemented **9 Playwright E2E tests** covering all main, alternative, and exception flows.
- **Results:** 100% pass rate (**9/9 passed in 20.1s**).
- **Assertions:** Every test asserts both the DOM status badge and the exact approval trail length and field values via read-back.
- HTML report preserved in [`evidence/m3/playwright-uc5-uc6/`](../../evidence/m3/playwright-uc5-uc6/).

---

## 3. Deliverable B: Usability & Accessibility Testing (WCAG 2.1 AA)

### 3.1 Task & Keyboard Navigation Tests (`tests/team/a11y/usability.spec.ts`)
- **3/3 passed in 4.3s**:
  1. *Workflow 1 Task Test:* Submits negative amount (-50.00), asserts business rule rejection banner, corrects amount to 65.00, asserts draft creation confirmation.
  2. *Workflow 2 Task Test:* Complete review cycle with feedback verification.
  3. *Keyboard-Only Navigation Test:* Tab/Enter only navigation on `/requests/new`. Focus reaches title -> line items -> submit button in strict semantic order and submits via keyboard `Enter`.

### 3.2 Automated Audits & UI Fix (Before vs. After)
Audited 4 core screens using `@axe-core/playwright` and Google Lighthouse. Identified 5 serious accessibility violations on `/requests/new` (missing form labels, contrast, lack of landmarks).

**UI Remediation (Commit `53f7568` on `frontend/src/pages/NewRequest.tsx`):**
- Bound explicit HTML `<label htmlFor="...">` elements with input IDs.
- Added semantic `<main>` role landmark and increased color contrast ratios.

| Screen | Lighthouse A11y (Before) | Lighthouse A11y (After) | Axe Violations (Before) | Axe Violations (After) | Status |
|---|---|---|---|---|---|
| `/requests/new` | **75 / 100** | **100 / 100** (+25) | **5 Serious** | **0** | **FIXED** |
| `/login` | 92 / 100 | 92 / 100 | 0 | 0 | PASS |
| `/` (List) | 88 / 100 | 88 / 100 | 0 | 0 | PASS |
| `/requests/:id` | 91 / 100 | 91 / 100 | 0 | 0 | PASS |

Evidence: [`evidence/m3/lighthouse/`](../../evidence/m3/lighthouse/) and [`evidence/m3/axe/`](../../evidence/m3/axe/).

---

## 4. Deliverable C: Defensive Security & Supply Chain Audits

### 4.1 Access Decision Matrix (`tests/team/security/access_control.spec.ts`)
- **5/5 tests passed in 7.9s** validating dual-layer access decisions via direct REST API and UI:
  1. *Manager Same Dept:* Allowed (200 OK -> `MANAGER_APPROVED`).
  2. *Manager Other Dept:* Denied (403 Forbidden).
  3. *Other Employee:* Denied (404 Not Found on view, 403 Forbidden on edit).
  4. *Finance:* Allowed (200 OK -> `FINANCE_APPROVED`).
  5. *Employee Owner:* Denied self-approval (403 Forbidden).

### 4.2 Passive OWASP ZAP Proxy Scan (`evidence/m3/zap/`)
- Intercepted traffic across Workflow 1 and Workflow 2 through ZAP 2.17.0 proxy:
  - **High:** 0 | **Medium:** 12 | **Low:** 26 | **Informational:** 20
  - *Key Weaknesses:* Missing Anti-clickjacking Header (`X-Frame-Options` CWE-1021) and Missing CSP (CWE-693).

### 4.3 Software Supply Chain Audits
- **Frontend (`npm audit`):** 168 packages scanned; identified 2 High-severity CVEs in dev bundler (`vite` <= 6.1.6 SSRF and `source-map-js` ReDoS).
- **Backend (`dependency-check:check`):** Audited Maven classpath; documented NVD 2.0 API authentication requirements in [`evidence/m3/security/dependency-check-log.txt`](../../evidence/m3/security/dependency-check-log.txt).

---

## 5. Deliverable D: Performance & Recovery Under Stress

### 5.1 k6 Load Testing (`docs/m3/performance.md`)
- **Pre-set Limit:** $T_{p95} \le 250\text{ ms}$, unexpected failures $\le 0.1\%$.
- **Target Endpoint:** `GET /api/requests` (Scoped relational query with authorization).
- **Empirical Results (4 runs, 60s sustained each — 11,318 requests total):**
  - Run 1 (1 VU): 981 reqs, 16.31 req/s, **p95 = 16.78 ms**, 0% failures (**PASS**).
  - Run 2 (1 VU replicate): 998 reqs, 16.59 req/s, **p95 = 13.12 ms**, 0% failures (**PASS**).
  - Run 3 (5 VUs): 4,638 reqs, 77.10 req/s, **p95 = 19.19 ms**, 0% failures (**PASS**).
  - Run 4 (5 VUs replicate): 4,701 reqs, 78.08 req/s, **p95 = 18.60 ms**, 0% failures (**PASS**).

### 5.2 Automated Failure & Recovery Test (`tests/team/perf/recovery.spec.ts`)
- Halts PostgreSQL container mid-transaction, attempts approval, verifies clean rollback (no partial write), restores container, retries approval, and asserts final state.
- **Assertion:** Exactly **0 duplicate approval-trail rows** created (`approvals.length === 2`, exactly 1 `APPROVE` record). Passed in 8.6s.

---

## 6. Deliverable E: Defect Management & Root Cause Analysis

- **GitHub Issue Drafts:** Authored 6 actionable drafts (`docs/m3/defects/issue-01.md` through `issue-06.md`) linked to Risk Register IDs (`PR-04`, `PR-07`, `PR-08`, `PJ-01`).
- **5 Whys RCA (`docs/m3/defects/rca.md`):** Traced root causes for Security Headers omission and UI Form Accessibility barrier.
- **Diagrams:**
  - *Fishbone Diagram:* [`evidence/m3/defects/fishbone_security.png`](../../evidence/m3/defects/fishbone_security.png).
  - *Pareto Chart:* [`evidence/m3/defects/pareto.png`](../../evidence/m3/defects/pareto.png) proving 89.6% of issues stem from Security Headers and Accessibility.

---

## 7. Exit Criteria Verification Summary

| Exit Criteria ID | Target Threshold | Member 3 Observed Result | Status |
|---|---|---|---|
| **EC-1** | 100% Pass on UC5/UC6 Playwright flows | 9/9 passed in 20.1s | **MET** |
| **EC-2** | Under k6 load, p95 $\le$ 500 ms, failures < 1%; 0 duplicate rows on recovery | p95 $\le$ 19.19 ms, 0.00% failures; exactly 0 duplicate rows | **MET** |
| **EC-3** | 100% pass on role access matrix, Lighthouse A11y $\ge$ 90, 0 critical axe violations | 5/5 access tests passed, Lighthouse = 100/100, 0 axe violations | **MET** |
