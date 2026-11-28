import os
import re

base_dir = r"C:\Users\DELL\.gemini\antigravity\scratch\expense-approval"

def read_file(rel_path):
    p = os.path.join(base_dir, rel_path)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return ""

sys_scope = read_file("docs/team/01_system_and_scope.md")
test_plan = read_file("docs/team/07_test_plan_and_estimation.md")
risk_exit = read_file("docs/team/08_risk_register_and_exit_criteria.md")
monitor_comp = read_file("docs/team/09_monitoring_and_completion.md")
weekly_prog = read_file("docs/team/10_weekly_progress_member2.md")
m1_report = read_file("docs/team/Member1_PDF_Section.md")
m2_report = read_file("docs/team/Member2_PDF_Section.md")
m3_report = read_file("docs/m3/report/Member3_Quality_Engineering_Report.md")
m1_ai = read_file("docs/team/ai_use_member1.md")
m2_ai = read_file("docs/team/ai_use_member2.md")
m3_ai = read_file("docs/m3/ai-use-record.md")

header = """# FAST National University of Computer and Emerging Sciences
## Department of Computer Science — Islamabad Campus
### SE3002: Software Quality Engineering (Fall 2026)
# Final Project Quality Engineering Report: Automated Testing of Expense Approval MIS

---

### Project Information & Group Details

| Parameter | Specification |
|---|---|
| **Course** | SE3002: Software Quality Engineering |
| **Academic Term** | Fall 2026 |
| **Section** | Section SE-C |
| **System Under Test** | Expense Approval Management Information System (Spring Boot 4.1, PostgreSQL 16, React 19) |
| **Repository URL** | https://github.com/Anfey-SE/expense-approval |
| **Upstream Repository** | https://github.com/LijuanTang94/expense-approval (MIT Licence) |
| **Baseline Commit** | `ae596c3` |
| **Final Integration** | Merged across PRs #14 through #21 to `master` |
| **Group Members** | **Member 1: Amna Hafeez (24I-3112) —** Static Analysis, White-Box Unit Testing, PIT Mutation, CI Quality Gate, UC1/UC2<br>**Member 2: Humna Attique (24I-3097) —** Test Management Lead, OpenAPI Specification, EP/BVA Test Data Generator, API Test Suite, UC3/UC4, PDF Compilation<br>**Member 3: Uswa Shafiq (24I-0761) —** Usability & WCAG 2.1 AA Accessibility, Defensive Security, k6 Performance, ACID Failure Recovery, UC5/UC6, Defect RCA |

---

## Executive Summary & Work Allocation Matrix

This document compiles the complete, end-to-end quality engineering deliverables for the Expense Approval MIS project. Testing was conducted across the software lifecycle, encompassing static code analysis, statement/branch white-box coverage, mutation analysis with custom domain mutators, specification-based equivalence partitioning and boundary value analysis, REST API integration, browser end-to-end automation, non-functional accessibility and defensive security audits, and load/stress recovery benchmarks.

### Work Division and Component Traceability

| Functional Area | Primary Deliverables | Lead Author | Marks Weighting | Status |
|---|---|---|---|---|
| **System & Scope** | Baseline verification, 16 functional requirements, 4 business rules, 3 user roles, seed data & environment reset scripts | Member 1 (Shared) | 5 Marks | Complete (docs/team/01_system_and_scope.md) |
| **Static Analysis** | SonarQube Community scan, file/method complexity, 0 debt/code smells, documentation of upstream security rules | Member 1 (24i-3112) | 5 Marks | Complete (Rating A Reliability, Rating D Security documented) |
| **White-Box Testing** | JaCoCo 100% line/branch enforcement on 6 core classes, MCC & MC/DC on `assertCanDecide`, 136 team unit tests | Member 1 (24i-3112) | 16 Marks | Complete (100% JaCoCo, 100% MC/DC) |
| **Mutation Testing** | PIT mutation analysis, 2 custom domain mutators (department check, approver swap), 99% mutation score | Member 1 (24i-3112) | 8 Marks | Complete (81/82 mutants killed in DEFAULTS) |
| **CI Quality Gate** | GitHub Actions pipeline enforcing coverage, SonarQube quality gate, and mutation thresholds | Member 1 (24i-3112) | Shared | Complete (Blocked PR #3 demo, Fix PR #5 merged) |
| **Test Plan & Estimation** | 5-week schedule, 3-point effort estimation ($E = \frac{O+4M+P}{6}$) vs actuals, variance analysis | Member 2 (24i-3097) | 5 Marks | Complete (82.50h actual vs 89.81h expected, variance -8.1%) |
| **Risk & Exit Criteria** | 5x5 Risk Matrix (8 product risks, 2 project risks), 3 measurable exit criteria | Member 2 (24i-3097) | 5 Marks | Complete (EC-1, EC-2, EC-3 verified MET) |
| **Monitoring & Completion** | Weekly GQM metric tracking, test completion report, release recommendation | Member 2 (24i-3097) | 5 Marks | Complete (GO FOR RELEASE, 0 open Critical/High defects) |
| **OpenAPI & Test Data Generator** | OpenAPI 3.0.3 spec (11 endpoints), automated EP/BVA generator (257 test cases), live regeneration demo | Member 2 (24i-3097) | 7 Marks | Complete (openapi.yaml, generate_test_data.py) |
| **API & Integration Tests** | 120 API tests (EP, BVA, state transitions, idempotency, concurrent double-approve, coverage tracking) | Member 2 (24i-3097) | 10 Marks | Complete (120/120 passing in CI job python-api-tests) |
| **Usability & Accessibility** | Lighthouse audits, axe-core scans, UI remediation commit `53f7568`, keyboard navigation tests | Member 3 (24i-0761) | 5 Marks | Complete (Lighthouse 75 to 100/100, 0 axe serious violations) |
| **Defensive Security** | 5-role access decision matrix, OWASP ZAP passive scan (0 High), npm audit, Dependency-Check | Member 3 (24i-0761) | 6 Marks | Complete (58 ZAP alerts: 0 High, 12 Medium, 26 Low, 20 Info) |
| **Performance & Recovery** | k6 load tests (4 runs, 11,318 requests, p95 13-19 ms vs 250 ms SLA), PostgreSQL failure recovery test | Member 3 (24i-0761) | 5 Marks | Complete (p95 <= 19.19 ms, 0.00% errors, 0 duplicate rows) |
| **Defect Management & RCA** | 6 GitHub issue drafts, 5 Whys root cause analysis, Pareto distribution (89.6% concentration), Fishbone | Member 3 (24i-0761) | 5 Marks | Complete (docs/m3/defects/, Pareto & Fishbone diagrams) |
| **Browser E2E Use Cases** | Playwright E2E automation for UC1 through UC6: M1 (UC1/UC2), M2 (UC3/UC4), M3 (UC5/UC6) | All Members | 12 Marks | Complete (25 Playwright tests passing: M1 8, M2 8, M3 9) |
| **AI Usage Transparency** | Prompts, tools consulted, output evaluation, verification procedures, and integrity statements | All Members | 6 Marks | Complete (M1, M2, M3 individual disclosures) |
| **Final Submission Package** | PDF compilation (M2), Git zip assembly (M1), Evidence verification (M3) | Member 2 Lead | 2 Marks | Complete (Project_24I-3112_24I-3097_24I-0761_C.pdf) |

---
"""

parts = [
    header,
    "\n# PART I: SHARED TEST MANAGEMENT & SYSTEM SPECIFICATION\n*(Prepared by Member 2 — Shared Test Management Lead)*\n\n",
    sys_scope,
    "\n---\n\n",
    test_plan,
    "\n---\n\n",
    risk_exit,
    "\n---\n\n",
    monitor_comp,
    "\n---\n\n",
    weekly_prog,
    "\n---\n\n# PART II: MEMBER 1 CONTRIBUTION (24i-3112)\n*(Static Analysis, White-Box Unit Testing, PIT Mutation Testing, CI Pipeline, UC1 & UC2)*\n\n",
    m1_report,
    "\n---\n\n# PART III: MEMBER 2 CONTRIBUTION (24i-3097)\n*(OpenAPI Specification, Automated EP/BVA Test Data Generator, API Integration Suite, UC3 & UC4)*\n\n",
    m2_report,
    "\n---\n\n# PART IV: MEMBER 3 CONTRIBUTION (24i-0761)\n*(Usability & Accessibility, Defensive Security, k6 Performance, ACID Failure Recovery, UC5 & UC6, Defect RCA)*\n\n",
    m3_report,
    "\n---\n\n# PART V: CONSOLIDATED AI ASSISTANCE DISCLOSURES\n\n",
    "### AI Usage Record — Member 1 (24i-3112)\n\n",
    m1_ai,
    "\n---\n\n### AI Usage Record — Member 2 (24i-3097)\n\n",
    m2_ai,
    "\n---\n\n### AI Usage Record — Member 3 (24i-0761)\n\n",
    m3_ai,
    """
---

### Appendix: Git Commit History & Build Traceability
- **Baseline Commit:** `ae596c3`
- **Member 1 Integration:** White-box unit tests, JaCoCo threshold enforcement, PIT custom mutators, CI quality gate (`0dfa6ce`, PR #5).
- **Member 2 Integration:**
  - PR #14: Parametrized state transition suite with per-case status and approval trail read-backs.
  - PR #15: Split repeated request idempotency tests and concurrent double-approval race condition verification.
  - PR #16: Automated OpenAPI test coverage fixture, coverage report, and endpoint gap tests.
  - PR #17: CI `python-api-tests` workflow job in `.github/workflows/ci.yml`.
  - PR #18: 6-week GQM progress reports and updated AI-assistance record.
  - PR #19: Review and merge of Member 3 quality engineering deliverables.
  - PR #20 & #21: Shared test management consolidation, embedded user screenshots, cryptographic test fix, and final PDF generation.
- **Member 3 Integration:** PR #19 (UC5/UC6 E2E automation, Lighthouse UI accessibility remediation `53f7568`, OWASP ZAP passive scan, k6 performance load, ACID failure recovery, 6 defect drafts and 5 Whys RCA).
- **Release Recommendation:** Unconditional **GO FOR RELEASE** (All 3 Exit Criteria EC-1, EC-2, EC-3 are 100% MET).
"""
]

combined = "".join(parts)

# Clean any remaining emojis
emoji_replacements = {
    '✅': '[Passed]',
    '🔄': '[In Progress]',
    '⚠️': '[Accepted]',
    '❌': '[Failed]',
    '✓': '[Passed]',
    '✗': '[Failed]',
    '✕': '[x]',
    '🟢': '[Approved]',
    '🎯': '',
    '👉': '',
    '📸': 'Figure: ',
    '🎉': '',
}
for k, v in emoji_replacements.items():
    combined = combined.replace(k, v)

# Clean excessive asterisks like **** or ***
combined = re.sub(r'\*{3,}', '**', combined)

out_path = os.path.join(base_dir, "docs", "team", "Final_Project_Report_Combined.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(combined)

print("Saved Final_Project_Report_Combined.md cleanly! Length:", len(combined))
