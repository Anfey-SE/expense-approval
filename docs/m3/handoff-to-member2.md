# Handoff to Member 2 (Test Management Lead)

**From:** Member 3 (roll no. 24i-0761, Section C)  
**To:** Member 2 (roll no. 24i-3097) — Shared Test Management Lead  
**Date:** November 2026  
**Branch:** `member3/usability-security-performance-uc5-uc6`  
**Effort Hours:** HOURS: to be filled by me  

---

## 1. Executive Summary

Member 3 has completed all assigned deliverables for the university Software Quality Engineering project (SE3002). All artifacts, test suites, evidence logs, reports, and defect drafts are committed to branch `member3/usability-security-performance-uc5-uc6`. No Member 1 or Member 2 baseline files were altered without documented cause.

---

## 2. Deliverables Summary for Integration

### 2.1 Use Cases 5 & 6 (Finance Workflow)
- **Specification:** [`docs/m3/use-cases.md`](use-cases.md) adheres strictly to the UC3/UC4 template.
- **Playwright Suite:** [`tests/team/e2e/tests/uc5-uc6-finance.spec.ts`](../../tests/team/e2e/tests/uc5-uc6-finance.spec.ts) (9 tests covering Main, Alternative, and Exception flows).
- **Execution Metric:** **9/9 passed in 20.1s**. HTML report archived in [`evidence/m3/playwright-uc5-uc6/`](../../evidence/m3/playwright-uc5-uc6/).

### 2.2 Usability & Accessibility (WCAG 2.1 AA)
- **Playwright Task & Keyboard Suite:** [`tests/team/a11y/usability.spec.ts`](../../tests/team/a11y/usability.spec.ts) (3 tests passed in 4.3s).
- **UI Bug Fix:** Resolved 5 serious accessibility violations in `frontend/src/pages/NewRequest.tsx` (Commit `53f7568`).
- **Audit Metrics:**
  - `/requests/new` Lighthouse A11y jumped from **75 to 100/100**.
  - Axe violations reduced from **5 Serious to 0**.
  - Audits preserved in [`evidence/m3/lighthouse/`](../../evidence/m3/lighthouse/) and [`evidence/m3/axe/`](../../evidence/m3/axe/).

### 2.3 Defensive Security & Supply Chain Audits
- **Access Decision Suite:** [`tests/team/security/access_control.spec.ts`](../../tests/team/security/access_control.spec.ts) (**5/5 passed in 7.9s**).
- **OWASP ZAP Passive Scan:** 58 alerts (0 High, 12 Medium, 26 Low, 20 Info). Report in [`evidence/m3/zap/`](../../evidence/m3/zap/).
- **Dependency Audits:**
  - `npm audit`: 2 High severity vulnerabilities identified in dev dependencies (`vite` SSRF/path traversal and `source-map-js`).
  - Maven dependency-check: Recorded NVD 2.0 API requirement log in [`evidence/m3/security/dependency-check-log.txt`](../../evidence/m3/security/dependency-check-log.txt).

### 2.4 Performance & Failure Recovery
- **k6 Load Tests:** 4 continuous 60s runs on `GET /api/requests` (11,318 requests total):
  - Run 1 (1 VU): 981 reqs, $p95 = 16.78\text{ ms}$, 0% failures.
  - Run 2 (1 VU replicate): 998 reqs, $p95 = 13.12\text{ ms}$, 0% failures.
  - Run 3 (5 VUs): 4,638 reqs, $p95 = 19.19\text{ ms}$, 0% failures.
  - Run 4 (5 VUs replicate): 4,701 reqs, $p95 = 18.60\text{ ms}$, 0% failures.
  - All runs beat the $p95 \le 250\text{ ms}$ SLA by over 10x. Logs in [`evidence/m3/perf/`](../../evidence/m3/perf/).
- **Failure & Recovery Spec:** [`tests/team/perf/recovery.spec.ts`](../../tests/team/perf/recovery.spec.ts) (halted PostgreSQL container mid-transaction; verified clean rollback, restored container, retried approval, and confirmed **exactly 0 duplicate approval-trail rows**).

### 2.5 Defect Management & RCA
- **Issue Drafts:** 6 issues ready for GitHub triage in [`docs/m3/defects/issue-01.md` through `issue-06.md`](defects/).
- **Root Cause Analysis:** 5 Whys and CAPA documented in [`docs/m3/defects/rca.md`](defects/rca.md).
- **Diagrams:** Fishbone diagram ([`evidence/m3/defects/fishbone_security.png`](../../evidence/m3/defects/fishbone_security.png)) and Pareto chart ([`evidence/m3/defects/pareto.png`](../../evidence/m3/defects/pareto.png)).

---

## 3. Exit Criteria Status Mapping

| Exit Criteria | Target | Member 3 Status |
|---|---|---|
| **EC-1 (Functional Pass Rate)** | 100% Pass on UC5/UC6 | **MET** (9/9 passed) |
| **EC-2 (Performance & Recovery)** | p95 $\le$ 500ms, < 1% failures; 0 duplicate rows | **MET** (p95 $\le$ 19.19ms, 0% failures, 0 duplicate rows) |
| **EC-3 (Security & Accessibility)** | 100% role access pass; Lighthouse A11y $\ge$ 90; 0 critical axe | **MET** (5/5 access passed, Lighthouse 100/100, 0 axe criticals) |

---

## 4. Effort Hours & Personal Contributions

- **Effort Hours:** HOURS: to be filled by me
- **AI Tool Tracking:** Completely logged in [`docs/m3/ai-use-record.md`](ai-use-record.md).
- **Full Assignment Prompts:** Recorded in [`docs/m3/prompts.md`](prompts.md).
