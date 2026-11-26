# Prompt part 2 for Antigravity: decision tables, state transitions, boundary tests (Member 1)

Same hard rules as before: only real tool output as evidence, quote code verbatim from the source with file and line numbers, tests only under `tests/team/unit/`, no weakening of existing tests, no `continue-on-error` or `|| true`, update `docs/team/ai_use_member1.md` and `docs/team/viva_notes_member1.md`, commit under my own git identity.

## Branch
Do NOT push to `member1/white-box-unit-tests` while the first PR's CI run is in progress. Create a new branch from it, `member1/decision-state-boundary-tests`, and work there. Open a separate PR later when I ask.

## Task A: Decision tables (docs/team/05_decision_tables.md)
For every business rule with two or more conditions, list ALL condition combinations and the expected outcome, then map each row to the exact test method that covers it (from `ExpenseServiceWhiteBoxTest`). Use the real code in `ExpenseService.assertCanDecide`, `submit` and `update` (quote it with line numbers).
- BR2/BR4 decision (`assertCanDecide`): conditions are (1) the request status awaits a decision, (2) caller's role owns the stage, (3) for a MANAGER: same department, (4) caller is not the requester. Show the full table, including combinations that are impossible or short-circuited, and say why.
- `submit`: conditions are caller is owner, status is DRAFT, at least one line item.
- `update`: owner, status DRAFT.
If a row has no test yet, add one in `tests/team/unit/` and say so.

## Task B: State transition table (docs/team/06_state_transitions.md)
Build a table of all 5 states (DRAFT, SUBMITTED, MANAGER_APPROVED, FINANCE_APPROVED, REJECTED) against the events: create/update, submit, approve (by the stage owner), reject (by the stage owner). For each cell mark allowed or disallowed, the resulting state or error code, and the test method that covers it. The brief requires: every allowed change tested, and at least one disallowed change from EACH state tested. Find any gap and add tests.

## Task C: Boundary value and equivalence tests for input limits
Add `tests/team/unit/com/sandy/expense/web/dto/ExpenseDtosValidationTest.java` using the Jakarta Bean Validation `Validator` (no Spring context, no database). Read the real constraints in `src/main/java/com/sandy/expense/web/dto/ExpenseDtos.java` and test, for EACH limit, just below, exactly at, and just above it, with ONE invalid value per test:
- title: not blank, max 200
- description: max 2000
- currency: exactly 3 characters (when present)
- items: not empty, max 100
- item description: not blank, max 200
- item category: not blank, max 40
- item amount: not null, positive, at most 10 integer digits and 2 decimal places
- item incurredOn: not null, not in the future (today is valid, tomorrow is invalid)
- decision comment: max 500
Also list the equivalence classes (valid and invalid groups) in `docs/team/07_boundary_tests.md` and map every test to its class and limit. Mention that Member 2 tests the same limits through the HTTP API, so these are unit-level and counted at the unit level only.

## Finish
Run the full team test suite, the JaCoCo check (the 100% scope must still pass), and PIT (DEFAULTS + custom, threshold 95). Report the new test count and the PIT score. If any number changes, update the docs with the real new values and say what changed. Show me a short summary and wait. Do not push until I say so.
