# Prompts and AI Guidance Log — Member 3 (24i-0761)

This log records the prompts and instructions provided to the AI assistant (Antigravity) to assist with research, script drafting, and analysis for Member 3's focus areas, following university academic integrity guidelines (Section 7).

---

## Stage 0: Setup and Discovery Assistance
**Prompt:**
> "I am Member 3 (24i-0761) working on Section C of the SQE final project. My areas are UC5/UC6, accessibility/usability, defensive security, performance, and recovery. I am on branch `member3/usability-security-performance-uc5-uc6`.
> Let's start with Stage 0: Help me inspect our local environment and verify all required tools (Java 21, Maven wrapper, Node, Docker, k6). Help me map out the application's endpoints, roles, and test credentials from the existing repo docs, and set up our directory structure under `tests/team/`, `evidence/m3/`, and `docs/m3/`."

---

## Stage 1: UC5 and UC6 E2E Automation
**Prompt:**
> "Review Member 2's UC3 and UC4 specifications in `docs/team/06_use_cases_member2.md` and help me draft the use case specifications for UC5 (Finance Approval) and UC6 (Finance Rejection) in `docs/m3/use-cases.md`. Each use case must have an actor, preconditions, trigger, main flow, at least 2 alternative flows, and at least 2 exception flows.
> Then, help me structure the Playwright test automation in `tests/team/e2e/tests/uc5-uc6-finance.spec.ts` to assert both the on-screen status badge and the exact approval trail read-back for every flow."

---

## Stage 2: Usability and Accessibility (WCAG 2.1 AA)
**Prompt:**
> "For Stage 2:
> 1. Help me draft automated Playwright usability task tests for both workflows, including a business rule negative-input correction flow and a Tab/Enter keyboard navigation test.
> 2. Help me run Google Lighthouse and Axe-core scans on our four main screens (`/login`, `/`, `/requests/new`, `/requests/:id`).
> 3. After we review the findings in `docs/m3/a11y-issues.md`, assist me in implementing the semantic labels and landmark fixes on `frontend/src/pages/NewRequest.tsx`, and re-running the audits to produce the before/after comparison."

---

## Stage 3: Defensive Security and Dependency Audits
**Prompt:**
> "For Stage 3:
> 1. Help me map the routes and permissions across all 5 roles into an access matrix in `docs/m3/security.md`.
> 2. Help me implement the Playwright access control test suite verifying allowed and denied decisions via REST API and UI.
> 3. Guide me in configuring OWASP ZAP in passive proxy mode (no active scanning) to capture traffic during Playwright workflow execution.
> 4. Help me review the JWT token and authorization controls in `SecurityConfig.java` and `ExpenseService.java`, and run `npm audit` and Maven dependency check."

---

## Stage 4: Performance Load and Recovery Testing
**Prompt:**
> "For Stage 4:
> 1. Let's select `GET /api/requests` as our performance target. Help me formulate our pre-execution p95 latency and failure SLA targets with engineering justifications in `docs/m3/performance.md`.
> 2. Help me write a Grafana k6 script to run 1 VU (twice) and 5 VUs (twice) for 60 seconds each, saving the JSON summaries.
> 3. Help me write an automated failure-and-recovery test in Playwright that simulates a database failure during an approval state transition, verifies rollback, recovers the container, and asserts zero duplicate approval-trail rows."

---

## Stage 5: Defects Management and Root Cause Analysis
**Prompt:**
> "Help me formalize the genuine issues we observed into GitHub Issue drafts in `docs/m3/defects/` linking to Member 2's Risk Register IDs.
> For the two major defects (missing security headers and form accessibility), assist me in conducting a 5 Whys Root Cause Analysis with CAPA, and generating an Ishikawa fishbone diagram and a Pareto distribution chart."

---

## Stage 6: Final Reporting and Handoff
**Prompt:**
> "Help me draft my final Quality Engineering report section in `docs/m3/report/Member3_Quality_Engineering_Report.md` following the team template, and prepare `docs/m3/handoff-to-member2.md` with our exit criteria status. Make sure all effort hours remain marked as 'HOURS: to be filled by me' so I can record my actual human hours."
