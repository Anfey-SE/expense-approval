# Prompt for Antigravity: Member 1 work (SE3002 SQE Final Project)

You are helping Member 1 (24i-3112) of a 3-person university software-quality project. Work in the local clone of our fork of https://github.com/LijuanTang94/expense-approval (Java 21, Spring Boot 4.1, PostgreSQL + Flyway, JWT, React frontend, MIT licence). Baseline commit: ae596c382e61685841696a63efff094359aa4e59.

## Hard rules (marks depend on these)
- Never fabricate, hand-edit or "tidy" evidence. Every number in a report must come from a real tool run. Save raw outputs (JaCoCo XML/HTML, PIT report, Sonar export or screenshots, CI run URLs) under `docs/team/evidence/`.
- Our tests go ONLY in `tests/team/unit/` (upstream tests earn no marks). Do not edit upstream `src/test`.
- Do not add `continue-on-error` or `|| true` anywhere in CI.
- Keep an AI-use log in `docs/team/ai_use_member1.md`: for each task, the tool, the purpose, the output, and what was checked or changed. Save the prompts used.
- Commit in small commits under my own git identity on a feature branch, and open PRs. Never commit secrets.
- If something fails, say so. Do not weaken a test or threshold just to get green. Explain it instead.

## Already written (copy into the repo root, keeping paths)
`tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java`
`tests/team/unit/com/sandy/expense/service/AuthServiceWhiteBoxTest.java`
`tests/team/unit/com/sandy/expense/domain/DomainWhiteBoxTest.java`
These were written WITHOUT being compiled or run. Treat them as a draft: compile, run, and fix real mistakes. If a test fails because the source behaves differently from what the test assumed, tell me which one and why before changing it.

## Tasks, in order
1. **Baseline.** Run `./mvnw test` (Docker 29+: add `-DargLine="-Dapi.version=1.44"` per the README). Record the result, Java/Maven versions and OS. Write install / start / seed / reset commands (`docker compose up -d db`, `./mvnw spring-boot:run`, frontend `npm install && npm run dev`; seeding is automatic via DataSeeder; reset = `docker compose down -v`). Put them in `docs/team/01_system_and_scope.md`.
2. **Build wiring in pom.xml.** Add `build-helper-maven-plugin` so `tests/team/unit` is a test source root. Add the JaCoCo plugin (prepare-agent, report including XML, and a `check` rule). Scope for the 100% target: `com.sandy.expense.service.ExpenseService`, `AuthService`, `domain.RequestStatus`, `domain.ExpenseRequest`. Run the team tests plus upstream tests and report line and branch coverage. Justify any uncovered line in writing. Example already known: the `EMPTY_REQUEST` branch of `submit` is unreachable through HTTP because `CreateRequest.items` is `@NotEmpty`, but it is reachable at service level.
3. **System and scope doc** (`docs/team/01_system_and_scope.md`): upstream URL, licence, commit hash, DB (PostgreSQL via Flyway), roles (EMPLOYEE / MANAGER / FINANCE) and how they are enforced (`@PreAuthorize` + service checks), 8+ requirements (3+ per workflow) taken from the real code, 4 business rules with file and method references. Use these verified facts:
   - BR1 boundary: submit requires >= 1 line item (`ExpenseService.submit`, EMPTY_REQUEST); DTO limits: max 100 items, amount > 0 with 2 decimals, date not in the future.
   - BR2 decision with 2+ conditions: `assertCanDecide`, a manager must be in the same department AND the stage must be theirs, plus not-self.
   - BR3 state change: `RequestStatus.onApprove` / `approverRole`; REJECTED is reachable from SUBMITTED and MANAGER_APPROVED.
   - BR4: finance acts only on MANAGER_APPROVED (role owns the stage).
4. **MC/DC and CFG doc** (`docs/team/03_mcdc_and_cfg.md`). For `ExpenseService.assertCanDecide`: draw the CFG, count nodes/edges and compute cyclomatic complexity BY HAND (V(G) = E - N + 2, cross-check with predicates + 1). Build the full MCC table and the MC/DC independence pairs for each condition, and map each pair to the test method names I wrote (they carry `D1`..`D4` tags). Then compare with the SonarQube cognitive/cyclomatic number and explain any difference.
5. **SonarQube** (SonarCloud or local Docker), fed the JaCoCo XML. Capture complexity, duplication, code smells, bugs, vulnerabilities, coverage, technical debt, ratings. Explain each metric in plain words in `docs/team/02_static_analysis.md`.
6. **PIT mutation testing** (`pitest-maven` + `pitest-junit5-plugin`) on `com.sandy.expense.service.*` and `domain.*`, running only `tests/team` tests. Record the mutation score. Then create at least 2 CUSTOM mutators tied to our business rules (for example: drop the department check in `assertCanDecide`; replace the `approverRole` mapping of SUBMITTED/MANAGER_APPROVED; weaken the self-decision check). PIT custom mutators need a small plugin module registered via `ServiceLoader` (`MethodMutatorFactory`). Put it in `tools/pit-custom-mutators/` and explain how it works. Analyse at least 15 surviving mutants, classifying each as equivalent / missing test / weak assertion, and add tests to kill the killable ones. Report the score before and after.
7. **CI** (`.github/workflows/ci.yml`) on every pull request: Maven build, team + upstream tests (Testcontainers works on ubuntu-latest), JaCoCo check, SonarQube/SonarCloud scan, PIT with a `mutationThreshold` justified from the measured score. No `continue-on-error`, no `|| true`. Then produce two PRs: one the pipeline BLOCKS (for example a PR that weakens a test or drops a department check, so PIT or coverage fails) and one fix PR that fails before and passes after. Record the run URLs.
8. **Hand-off notes** for the other two members: where the CI skeleton is and how to run the team tests locally.

## Viva readiness
After each task, write a short plain-English note of what the code does and why, in `docs/team/viva_notes_member1.md`. I must be able to explain every assertion and predict which tests and gate break after a rule change (for example changing the department rule or adding a new transition).

Start with task 1 and tell me the exact commands and results before moving on.
