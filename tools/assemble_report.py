import os

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

header = """# SE3002 Software Quality Engineering — Final Project Report
## Automated Testing of an Open-Source Management Information System
### System Under Test: Expense Approval MIS (Spring Boot 4.1 + React 19 + PostgreSQL 16)

---

### Project & Team Metadata

| Field | Detail |
|---|---|
| **Course** | SE3002 Software Quality Engineering, Fall 2026 |
| **Institution** | FAST National University of Computer and Emerging Sciences |
| **Section** | Section C |
| **Repository URL** | `https://github.com/Anfey-SE/expense-approval` |
| **Upstream URL** | `https://github.com/LijuanTang94/expense-approval` (MIT Licence) |
| **Baseline Commit** | `ae596c3` |
| **Final Integration Commit** | Merged across PRs #14, #15, #16, #17, #18, #19 to `master` |
| **Team Members** | **Member 1:** 24i-3112 (Static Analysis, White-Box, Mutation, CI Gate, UC1/UC2)<br>**Member 2:** 24i-3097 (Shared Test Management Lead, OpenAPI, EP/BVA Data Generator, API Suite, UC3/UC4, PDF)<br>**Member 3:** 24i-0761 (Usability/A11y, Defensive Security, k6 Perf, ACID Recovery, UC5/UC6, Defect RCA) |

---

## Executive Summary & Work Allocation

This report presents the complete quality engineering deliverables for the **Expense Approval MIS**, satisfying the 120-mark SQE rubric through automated multi-level testing, quantitative metrics, defect root-cause analysis, and continuous integration gating.

### Work Division & Responsibility Matrix

| Area | Deliverable | Lead Member | Marks | Verification Status |
|---|---|---|---|---|
| **System & Scope** | Baseline commit, requirements (16), business rules (4), roles (3), test basis, seed data, reset procedure | M1 Lead (Shared) | 5 | Complete (`docs/team/01_system_and_scope.md`) |
| **Static Analysis** | SonarQube Community run, complexity analysis, clean maintainability (0 smells), vulnerability documentation | Member 1 (24i-3112) | 5 | Complete (Rating A Reliability, Rating D Security documented) |
| **White-Box Testing** | JaCoCo 100% line/branch gate on 6 core classes, MCC & MC/DC on `assertCanDecide`, 136 team unit tests | Member 1 (24i-3112) | 16 | Complete (100% JaCoCo, 100% MC/DC) |
| **Mutation Testing** | PIT mutation testing, 2 custom business-rule mutators, 99% mutation score, survivor analysis | Member 1 (24i-3112) | 8 | Complete (81/82 mutants killed in DEFAULTS, 98% in ALL) |
| **CI Quality Gate** | GitHub Actions pipeline enforcing coverage, SonarQube, PIT, and demo of blocked PR vs fix PR | Member 1 (24i-3112) | Shared | Complete (Blocked PR #3, Fix PR #5 merged) |
| **Test Plan & Estimation** | 5-week schedule, 3-point estimation vs actuals, variance analysis | Member 2 (24i-3097) | 5 | Complete (82.5h vs 89.81h expected, variance -8.1%) |
| **Risk & Exit Criteria** | 5x5 Risk Register (8 product, 2 project), 3 measurable exit criteria | Member 2 (24i-3097) | 5 | Complete (EC-1, EC-2, EC-3 all 100% MET) |
| **Test Monitoring** | Weekly tracking, GQM metrics, completion report, release recommendation | Member 2 (24i-3097) | 5 | Complete (GO FOR RELEASE, 0 open Critical/High defects) |
| **OpenAPI & Generator** | Complete OpenAPI 3.0 spec (11 endpoints), automated EP/BVA generator (257 cases), live regeneration demo | Member 2 (24i-3097) | 7 | Complete (`openapi.yaml`, `generate_test_data.py`) |
| **API & Integration** | 120 API tests (EP, BVA, state transitions, idempotency, concurrent double-approve, coverage fixture) | Member 2 (24i-3097) | 10 | Complete (120/120 passing in CI job `python-api-tests`) |
| **Usability & A11y** | Lighthouse audit, `@axe-core` scans, UI bug fix (`53f7568`), keyboard-only navigation test | Member 3 (24i-0761) | 5 | Complete (Lighthouse 75->100, 0 axe serious violations) |
| **Defensive Security** | 5/5 role access matrix, OWASP ZAP passive scan (0 High), `npm audit`, Maven Dependency-Check | Member 3 (24i-0761) | 6 | Complete (58 ZAP alerts: 0 High, 12 Med, 26 Low, 20 Info) |
| **Performance & Recovery** | k6 load testing (4 runs, 11,318 reqs, p95 13-19 ms vs 250 ms SLA), PostgreSQL failure recovery | Member 3 (24i-0761) | 5 | Complete (p95 <= 19.19 ms, 0% errors, 0 duplicate rows) |
| **Defect RCA & Pareto** | 6 GitHub issue drafts, 5 Whys root cause analysis, Pareto chart (89.6% concentration), Fishbone diagram | Member 3 (24i-0761) | 5 | Complete (`docs/m3/defects/`, Pareto & Fishbone charts) |
| **E2E Use Cases** | Playwright E2E automation for UC1-UC6 (2 per member): M1 (UC1/UC2), M2 (UC3/UC4), M3 (UC5/UC6) | All Members | 12 | Complete (25 Playwright tests passing: M1 8, M2 8, M3 9) |
| **AI Use Records** | Prompts, tools, outputs, manual verification, and reflection | All Members | 6 | Complete (M1, M2, M3 individual disclosures) |
| **Final Package** | PDF compilation (M2), Git zip assembly (M1), Evidence verification (M3) | M2 Lead | 2 | Complete (`Project_24I-3112_24I-3097_24I-0761_C.pdf`) |

---
"""

parts = [
    header,
    "\n# PART I: SHARED TEST MANAGEMENT & SYSTEM FOUNDATION\n*(Led by Member 2 — Shared Test Management Lead)*\n\n",
    sys_scope,
    "\n---\n\n",
    test_plan,
    "\n---\n\n",
    risk_exit,
    "\n---\n\n",
    monitor_comp,
    "\n---\n\n",
    weekly_prog,
    "\n---\n\n# PART II: MEMBER 1 CONTRIBUTION (24i-3112)\n*(Static Analysis, White-Box Testing, PIT Mutation, CI Quality Gate, UC1 & UC2)*\n\n",
    m1_report,
    "\n---\n\n# PART III: MEMBER 2 CONTRIBUTION (24i-3097)\n*(OpenAPI Specification, EP/BVA Test Data Generator, API & Integration Testing, UC3 & UC4)*\n\n",
    m2_report,
    "\n---\n\n# PART IV: MEMBER 3 CONTRIBUTION (24i-0761)\n*(Usability & Accessibility, Defensive Security, k6 Performance, ACID Failure Recovery, UC5 & UC6, Defect RCA)*\n\n",
    m3_report,
    "\n---\n\n# PART V: CONSOLIDATED AI USE DISCLOSURES\n\n### AI Use Record — Member 1 (24i-3112)\n",
    m1_ai,
    "\n---\n\n### AI Use Record — Member 2 (24i-3097)\n",
    m2_ai,
    "\n---\n\n### AI Use Record — Member 3 (24i-0761)\n",
    m3_ai,
    """
---

### Appendix: Git Commit History & Release Verification
- **Baseline Commit:** `ae596c3`
- **Member 1 Commits:** Static analysis, white-box unit tests, JaCoCo gate, PIT custom mutators, CI quality gate (`0dfa6ce`, PR #5).
- **Member 2 Commits:** 
  - PR #14: Parametrized state transitions with per-case status & approval trail read-backs.
  - PR #15: Split idempotency tests with concurrent double-approve race condition test.
  - PR #16: OpenAPI coverage fixture, automated report, and coverage gap tests.
  - PR #17: CI `python-api-tests` GitHub Actions job.
  - PR #18: 6-week GQM progress reports and AI use disclosure.
  - PR #19: Review and merge of Member 3's quality engineering deliverables.
- **Member 3 Commits:** PR #19 (UC5/UC6 E2E, Lighthouse accessibility UI fix `53f7568`, OWASP ZAP passive scan, k6 performance load, ACID failure recovery, 6 defect drafts and 5 Whys RCA).
- **Release Verdict:** All exit criteria (EC-1, EC-2, EC-3) 100% MET. Unconditional **GO FOR RELEASE**.
"""
]

combined = "".join(parts)
out_path = os.path.join(base_dir, "docs", "team", "Final_Project_Report_Combined.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(combined)

print("Saved Final_Project_Report_Combined.md successfully! Length:", len(combined))
