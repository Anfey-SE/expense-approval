# Initial Assignment Prompt — Member 3 (24i-0761)

```text
NOTE: pom.xml is in the project root, there is no "backend" folder. Java 21 is required and installed. Use .\mvnw.cmd (Windows PowerShell) instead of mvn. Docker, Node and npm are installed.ROLE
You are helping me, Member 3 (roll no. 24i-0761), finish my part of a university Software Quality Engineering final project (SE3002). I am a beginner with these tools. Work step by step, run real commands, and complete this assignement ,dont leave anything behind .

PROJECT CONTEXT
- Repo: open-source Expense Approval MIS (Spring Boot backend + React frontend, MIT licence). Group repo: https://github.com/Anfey-SE/expense-approval . I am already on branch member3/usability-security-performance-uc5-uc6 (created from an up-to-date master).
- Module under test: Expense Requests. Workflow 1 = Submit Expense Request (employee creates a DRAFT with line items and submits it, status becomes SUBMITTED, approval-trail row added). Workflow 2 = Review Expense Request (manager in the same department approves -> MANAGER_APPROVED, then finance approves -> FINANCE_APPROVED; a rejection sets REJECTED). Shared record: ExpenseRequest status and approval trail.
- Group: 24i-3112 (Member 1: static analysis, unit tests, mutation, CI), 24i-3097 (Member 2: OpenAPI spec, EP/BVA generator, API tests, UC3/UC4, test plan, RTM, risk register, monitoring report; their PRs #12 and #13 are merged to master), 24i-0761 (me, Member 3), Section C.
- My deliverables: (A) UC5 and UC6 specs and Playwright tests, (B) usability and accessibility, (C) defensive security, (D) performance and recovery, (E) defect management and RCA, (F) report sections and a results summary for Member 2.

HARD RULES (do not break these)
1. NEVER fabricate or edit evidence. Every number, screenshot, report, log, test result and defect must come from a real run you actually executed in this environment. If something fails or cannot run, say so plainly and show the error. Do not invent results, scores, hours or defects.
2. Never invent defects. Log only genuine bugs or weaknesses you actually observed, with real severity. If few exist, say so.
3. Do not invent my effort hours. Write "HOURS: to be filled by me" in effort logs. Only record actual time I tell you.
4. Security work is passive and local only: no active scanning, no spider, no fuzzing, no brute force, no attacks on anything except my local copy with synthetic test data.
5. Do not modify Member 1 or Member 2 files except where a documented fix requires it. Put all my work under tests/team/<area>/, evidence/m3/, docs/m3/. Do not touch master; commit only to my branch in small commits per area with clear messages. Do not push without asking me. Do not set a git author other than what is already configured.
6. Never use continue-on-error or "|| true" in any CI file. Do not break the existing CI (SonarQube, tests, PIT).
7. First read the existing repo docs (README, docs/, tests/team/, OpenAPI spec, risk register, RTM, test plan) and match their style, IDs and folder layout. Reuse Member 2's UC3/UC4 Playwright tests as the template for mine.
8. Explain, don't just do. After each stage write docs/m3/explain-<stage>.md in plain language for a beginner: what was done, why, what each test asserts, what each tool output means, and 5 likely viva questions with short answers. I must be able to explain everything.
9. Log AI use: append every task you do to docs/m3/ai-use-record.md (columns: date, tool, purpose, output, what I should check or change) and keep this prompt in docs/m3/prompts.md.
10. Stop at the end of every stage and wait for my "continue". Show a short summary and anything I must check by hand.

STAGE 0: Setup and discovery
- Verify the branch, git user.name/email, and that history includes Member 2's work.
- Read the README and docs. Find: install, start, seed and reset commands; ports and URLs for backend and frontend; the database; the three roles and seeded test accounts (employee, manager, finance); the endpoints for both workflows; exact UI button names and messages.
- Check installed tools (Java, Maven, Node, npm, Docker, k6). List what is missing and tell me exactly how to install it. Wait for me if I must install something.
- Start the backend and frontend, seed data, and drive one request DRAFT -> SUBMITTED -> MANAGER_APPROVED -> FINANCE_APPROVED and another to REJECTED, to learn the real behaviour. Record exact element labels and messages.
- Create folders: tests/team/e2e, tests/team/a11y, tests/team/security, tests/team/perf, evidence/m3, docs/m3. Create docs/m3/effort-log.md, ai-use-record.md, prompts.md, defect-notes.md.
- Record environment details (OS, CPU, RAM, versions of Java, Node, browser, each tool, and the app commit hash) in docs/m3/environment.md.
- Install Playwright (Chromium), @axe-core/playwright, playwright-lighthouse/lighthouse, and prepare k6 and OWASP ZAP (Docker image zaproxy/zap-stable). Reuse an existing Playwright config if Member 2 made one.

STAGE 1: UC5 and UC6
- Write specs in docs/m3/use-cases.md using the same format as Member 2's UC3/UC4. UC5 = Finance approves a manager-approved request. UC6 = Finance rejects a manager-approved request. Each has: actor, preconditions, trigger, main flow, at least 2 alternative flows, at least 2 exception flows, postconditions. Verify every flow against the real app and drop or replace any flow the app does not support. Examples to check: approve/reject with comment or reason, view trail afterwards, request not yet manager-approved, non-finance user attempt, already finalised request, repeated request creating no duplicate trail row.
- Automate EVERY flow in Playwright under tests/team/e2e. Each test must assert the message/status shown on screen AND the postcondition (status and exact approval-trail row count, via UI or API read-back). Reset or create fresh data before each test so tests are independent. Run them all, fix flaky tests, and save the HTML report to evidence/m3/playwright-uc5-uc6/.

STAGE 2: Usability and accessibility
- Two Playwright task tests, one per workflow. In at least one, first submit a value the business rule rejects, assert the error message explains what to correct, correct it, and assert the success confirmation.
- One keyboard-navigation test: use only Tab/Enter, assert focus reaches each required field and the submit button in the expected order, and that the keyboard submits the form.
- Run Lighthouse (accessibility, best practices, SEO) on the key screen of each use case while logged in (use playwright-lighthouse or an equivalent login script) and a full @axe-core/playwright scan on the same screens. Save reports to evidence/m3/lighthouse/before and evidence/m3/axe/before.
- Create docs/m3/a11y-issues.md: merge duplicates (an issue found by both tools counts once) into a table with ID, screen, element, found by, user impact, proposed fix, severity, and linked risk-register ID (use the real IDs from Member 2's risk register).
- Fix ONE screen (in the React app), rerun both tools with the same scripts, save to .../after, and produce a before/after table (Lighthouse three scores, axe total and critical+serious counts). Make the fix on its own commit.

STAGE 3: Defensive security
- Map the routes and data for both workflows (from OpenAPI spec, Spring controllers, React routes) into docs/m3/security.md.
- Build an access matrix from what the source and documentation say each role SHOULD be able to do (employee owner, other employee, manager same department, manager other department, finance). Then write Playwright tests (tests/team/security) that verify at least 4 access decisions, including at least 1 allowed and 1 denied, through both UI and direct API calls. Record role, action, expected, observed, evidence for each. Any mismatch is a real defect: report it honestly.
- Run OWASP ZAP in PASSIVE mode as a proxy while the Playwright workflow tests run. Wait for the passive scan queue to empty, export the report to evidence/m3/zap/, and summarise alerts by risk level.
- Review at least two controls (e.g. token/session handling and role checks; optionally CORS and security headers), each with observation, corroborating source file and line, and verdict.
- Run dependency audits: OWASP Dependency-Check for Maven and npm audit for the frontend. Save raw outputs. Record the packages and versions checked. For each relevant finding give component, evidence, likely impact, recommended correction, and note false positives or unreachable code honestly.

STAGE 4: Performance and recovery
- Choose one operation (prefer a repeatable read such as getting an expense request or the pending list; justify the choice). BEFORE running anything, write the limits in docs/m3/performance.md: p95 response time limit and acceptable unexpected-failure percentage, with a justification.
- Write one k6 script. Run it with 1 virtual user twice and with 5 virtual users twice, at least 60 seconds each after the target users are reached (constant VUs), same build, machine and starting data (reset between runs). Save raw output and summary JSON for each run in evidence/m3/perf/. Report p95 (ms), requests per second and unexpected failure % per run, and compare with the limits. Interpret honestly, including when a limit is missed.
- Write one automated failure-and-recovery test for a state-changing operation (submit or an approval): simulate a dependency failure before the write completes (stop the DB container, or use a test double such as a mock/spy that makes the trail save fail once), verify the persisted state after the failure (no partial write), restore, retry, and assert the final state with ZERO duplicate approval-trail rows. Save the log. Report any real defect it reveals.

STAGE 5: Defects and RCA
- Turn every genuine finding from Stages 1-4 into a GitHub Issue draft (docs/m3/defects/issue-NN.md ready to paste, and use the gh CLI only if I approve): title, steps to reproduce, expected vs actual, severity, priority, category, status, triage decision, linked risk ID, evidence link.
- Pick at least 2 genuinely major defects and write RCA: 5 Whys, a fishbone diagram (generate it as an image), corrective action and preventive action.
- Build a Pareto chart by category from the real issue list (matplotlib or similar), save to evidence/m3/defects/pareto.png, and produce counts: open/closed, by severity, reopened.

STAGE 6: Report sections and handoff
- Write report sections as Markdown in docs/m3/report/: UC5/UC6, usability and accessibility, security, performance and recovery, defects and RCA, area ownership, AI-use record, evidence links. For every accessibility, security and performance finding include root cause, severity, risk, fix, and linked risk-register ID. Put screenshot file references where Member 2 should insert images.
- Write docs/m3/handoff-to-member2.md with the real numbers: Lighthouse scores before/after, axe critical counts, ZAP alert counts, Dependency-Check and npm audit counts by severity, role-matrix pass/fail, k6 p95 / requests per second / failure % for 1 and 5 users, recovery result (duplicate trail rows = ?), issues open/closed/by severity, 5 Whys and fishbone summary, Pareto top categories. Leave effort hours as "to be filled by me".
- Run my whole test set once from a clean state following only the documented commands, and report pass/fail. Make sure the existing CI would still pass. Show me git status and a list of commits. Do not push; give me the exact push and PR commands.

FINAL CHECKLIST (print at the end)
Every file created, every command to rerun each test, every item I must verify or fill manually (effort hours, my review of explanations), and the list of things that failed or could not be run.

Begin with Stage 0 now. Show your plan first, then proceed, and stop at the end of Stage 0 for my "continue".
```
