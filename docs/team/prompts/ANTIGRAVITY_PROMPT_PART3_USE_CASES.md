# Prompt part 3 for Antigravity: use cases UC1 and UC2 (Member 1)

Same hard rules as before: only real tool output as evidence, quote code verbatim with file and line numbers, never fabricate or edit evidence, no `continue-on-error` or `|| true`, commit under my identity (Anfey-SE <i243112@isb.nu.edu.pk>), do not push until I say so, update `docs/team/ai_use_member1.md` and `docs/team/viva_notes_member1.md`.

Create a new branch from the updated `master` called `member1/use-cases-uc1-uc2`.

## Scope
- UC1: Employee submits a draft with line items (Workflow 1).
- UC2: Employee edits a draft before submitting (Workflow 1).
Each needs a written specification AND Playwright automation of EVERY flow. The brief requires: preconditions, postconditions, at least 2 alternative flows and at least 2 exception flows per use case; each flow automated; each test asserts the DISPLAYED result and the POSTCONDITION.

## Step 1: Inspect the real application first (no writing yet)
Read the real code and UI, not assumptions. Report, with file and line numbers:
- Frontend routes and pages for creating, listing, editing and submitting a request (`frontend/src`, e.g. `NewRequest.tsx` and the detail/edit page). List every field, button and visible message, and the selectors you will use. Prefer `getByRole` / `getByLabel`; if the UI has no accessible labels, say so, and list any `data-testid` that already exist. Do NOT edit upstream frontend code just to add test ids without asking me.
- The seeded demo accounts and passwords: read `DataSeeder` and the README. Never invent credentials.
- What the UI really shows when: submit with no items, edit a SUBMITTED request, invalid amount, editing someone else's request, and any other error. Run the app and observe it, or read the code. Tell me which behaviours you could only read in code and not see running.
- Whether an employee can only see their own requests (list scoping) and how the UI hides or disables edit/submit for non-DRAFT requests.
Then show me the proposed list of flows per use case and WAIT for my approval. Flows must match what the app really does; the examples below are only placeholders:
  - UC1 alternatives: submit with several items; save draft then submit later. Exceptions: submit with no items rejected; submit by a user who is not the owner.
  - UC2 alternatives: add then remove an item; edit an amount then submit. Exceptions: edit a request that is already SUBMITTED; invalid amount value.

## Step 2: Specification docs
Write `docs/team/uc/UC1_submit_draft.md` and `docs/team/uc/UC2_edit_draft.md`. For each: ID, name, actor, goal, preconditions, trigger, main flow (numbered), at least 2 alternative flows (A1, A2...), at least 2 exception flows (E1, E2...), postconditions (success and failure), and a table mapping each flow ID to its Playwright test name, the assertion on the displayed result, and the assertion on the postcondition. Link to the business rules BR1 and BR3 where relevant (note that BR1 "at least one item" is only reachable through the UI/API if the UI allows an empty submit; say what really happens).

## Step 3: Playwright automation
- Tests go ONLY in `tests/team/e2e/` with their own `package.json` or a root config, plus `playwright.config.ts` using Chromium. Do not touch upstream `frontend` tests.
- Each test creates its own data with a unique title (for example a timestamp) so tests do not depend on each other or on a fresh database. Log in through the UI, or reuse a stored login state if you can show it is safe.
- Each test asserts BOTH (a) what the page displays (message, status badge, list row) and (b) the postcondition read back independently: reload the page and check the status, or call the backend API with the user's token via Playwright's `request` and check status and the approval trail. State which one you used and why.
- For exception flows, the test must prove nothing changed (for example status still DRAFT, no approval row added).
- One flow per test, descriptive names containing the flow ID (e.g. `UC1_E1_submitWithNoItems`).
- Run all tests twice. Save raw output (the list reporter text and the HTML report folder) under `docs/team/evidence/uc/`. If a test is flaky, say so; do not add arbitrary sleeps or retries to hide it.
- Report: number of tests, passed and failed, and any real defect you found in the app. A real defect must be logged as a GitHub Issue draft (title, steps, expected, actual, severity) in `docs/team/issues/`, not silently worked around.

## Step 4: CI
Do NOT add the Playwright tests to the required `quality-gate` job yet (they need the full app, a database and a browser). Instead tell me how it could be added as a separate job, with the cost in minutes, and wait for my decision.

## Finish
Show me a short summary with raw outputs of the two Playwright runs, the list of files changed, and wait. Do not push.
