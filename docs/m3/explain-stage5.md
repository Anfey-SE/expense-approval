# Stage 5 Explanation: Defects Management and Root Cause Analysis (RCA)

**Author:** Member 3 (roll no. 24i-0761, Section C)  
**Date:** November 2026  
**Audience:** Beginner / Peer Reviewers / Viva Examination Panel  

---

## 1. What Was Done and Why

In Stage 5, we formalized every genuine bug, weakness, and security finding observed across Stages 1–4 into actionable software engineering deliverables:
1. **GitHub Issue Drafts (`docs/m3/defects/issue-01.md` through `issue-06.md`):**
   - Transformed observed weaknesses into production-ready issue drafts complete with title, steps to reproduce, expected vs. actual, severity, priority, category, status, triage decision, linked risk-register IDs, and evidence links.
2. **Root Cause Analysis (RCA):**
   - Selected two major defects:
     - **Defect 1 (Security):** Missing Anti-Clickjacking & Security Headers (CWE-1021 / CWE-693).
     - **Defect 2 (Accessibility):** Missing Form Labels on New Request Page (WCAG 2.1 AA).
   - Applied the **5 Whys technique** to trace each symptom down to its root architectural and process cause.
   - Formulated actionable **Corrective and Preventive Action Plans (CAPA)**.
3. **Diagrammatic Quality Engineering Artifacts:**
   - Generated an **Ishikawa (Fishbone) Diagram** image (`evidence/m3/defects/fishbone_security.png`) analyzing causes across Environment, Architecture, Testing, and Standards.
   - Generated an empirical **Pareto Analysis Chart** (`evidence/m3/defects/pareto.png`) demonstrating the 80/20 distribution of system weaknesses.

---

## 2. What Each Tool Output & Artifact Represents

### 2.1 GitHub Issue Drafts
- **Traceability:** Every defect links directly to Member 2's Risk Register (`PR-07`, `PR-08`, `PR-04`, `PJ-01`), maintaining end-to-end traceability from requirements and risks to observed failures.
- **Triage Decisions:** Distinct operational statuses distinguish between issues already resolved in code (Issue #01 in commit `53f7568`), issues scheduled for upcoming security hardening sprints (Issues #02, #03, #04), and domain rule improvements (Issue #05).

### 2.2 5 Whys Analysis
- Iterative root cause discovery technique that moves past surface-level symptoms ("the header wasn't there") to uncover organizational and testing blind spots ("automated tests verified status codes but never asserted security headers").

### 2.3 Pareto Chart (`evidence/m3/defects/pareto.png`)
- The Pareto Principle (80/20 rule) proves that **89.6%** of all defects observed across the application stem from just two categories: **Security Headers** and **UI Accessibility**. Fixing these two areas yields the maximum return on software quality investment.

---

## 3. 5 Likely Viva Questions and Concise Answers

### Q1: What is the difference between a defect's severity and its priority?
**Answer:** **Severity** measures the technical impact of the defect on the system's operation or security (e.g., Critical, Major, Medium, Low). **Priority** indicates the business urgency of fixing it (e.g., P1 must fix immediately, P3 can wait for next release). For example, an accessibility barrier on the primary submission form is Major severity and P1 priority because it completely prevents disabled users from submitting expenses.

### Q2: How does the 5 Whys method help prevent recurring software bugs?
**Answer:** Fixing only the immediate symptom (e.g., adding a label to one input) leaves identical flaws elsewhere. The 5 Whys traces back to the systemic root cause (e.g., lack of automated accessibility linting and test assertions), allowing us to introduce preventive mechanisms (like `eslint-plugin-jsx-a11y` in CI) that prevent entire classes of future bugs.

### Q3: What is the purpose of an Ishikawa (Fishbone) diagram in quality engineering?
**Answer:** It is a structured cause-and-effect visualization tool that groups potential contributing factors into major categories (e.g., Methods, Tools, Environment, Architecture). It prevents tunnel vision by ensuring engineers consider procedural, architectural, and tooling causes rather than blaming a single developer.

### Q4: How does your Pareto chart inform test resource allocation?
**Answer:** Our Pareto analysis revealed that 38 out of 48 findings (79.2%) were security header omissions, and 5 (10.4%) were UI accessibility barriers. Together, these two areas account for **89.6%** of all issues. Therefore, quality assurance and developer efforts should be prioritized on Spring Security header configuration and accessible React form templates rather than low-yield areas.

### Q5: How did you ensure you complied with the rule against inventing defects?
**Answer:** Every single defect draft in `docs/m3/defects/` is backed by verifiable, reproducible evidence generated in our earlier stages: Issue #01 links to Axe JSON and Lighthouse HTML; Issues #02 and #03 link to ZAP proxy reports; Issue #04 links to `npm audit`; Issue #05 links to UC6 Playwright execution; and Issue #06 links to the Maven dependency-check log. No synthetic or hypothetical bugs were logged.
