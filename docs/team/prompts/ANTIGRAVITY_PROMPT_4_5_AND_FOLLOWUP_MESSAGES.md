# Prompt archive, part 2: follow-up messages and Prompts 4 and 5 (Member 1)

These are the follow-up messages and later prompts sent to Antigravity, written with the help of Claude (chat assistant). The three big prompts (ANTIGRAVITY_PROMPT_MEMBER1.md, ANTIGRAVITY_PROMPT_PART2.md, ANTIGRAVITY_PROMPT_PART3_USE_CASES.md) are in separate files. Smaller corrections typed earlier in the chat (SonarQube corrections, clean-cache reruns, ci.yml review fixes, author-email fix) are not reproduced here; they exist only in the chat transcript.

---------------------------------------------------------------------
## F1. Fix PR: after the failing test was confirmed
Push `fix/currency-validation` (commit 1 only). Do not add the fix yet. Open the PR titled "Test: currency accepts non-letter codes (expected to fail CI)". In the PR description write "Refs #N". Give me the run URL, the failing test name and the `Tests run:` line when CI finishes.

## F2. Fix PR: commit 2 instructions
The fix is `@Pattern(regexp = "[A-Za-z]{3}")` on `currency` in `ExpenseDtos.CreateRequest`, keeping `null` valid. First search the whole repo for any place that sends or stores a currency (DataSeeder, Flyway SQL, the frontend, upstream tests) and confirm none uses a non-letter or lowercase value. Report what you found. Add tests for "@@@", "US1", "usd" and "USD" in the same test class. Don't change or delete any existing test. Run the full team and upstream suites locally, show me the results, and wait before pushing.

## F3. Fix PR: before pushing commit 2
Amend commit 2 so `issue_currency_validation.md` is not in the repo root (remove it or move it to `docs/team/issues/`). Show raw `git show --stat HEAD` and the diff of the test file, which must have only added lines. Check the author is Anfey-SE <i243112@isb.nu.edu.pk>. Push normally (no force). Do not merge.

## F4. Evidence doc verification (09_blocked_and_fix_pr.md)
1. Verify every quoted log line against the zips (timestamp removed only), with a pass or fail per line.
2. Show the log lines proving Tests run: 157 and the real step names.
3. Show `git log --oneline --graph -10` for the commit hashes.
4. Match the PR #5 description on GitHub in the "Issue referenced" row.
5. State that the blocked-PR run stopped at the team-tests step, so Sonar and PIT did not run.
6. Quote the Sonar "QUALITY GATE STATUS" line.
7. Add a viva note on why the blocked PR fails.

## F5. Use cases: approval with changes
Redefine UC1 = "Employee submits a draft for approval" and UC2 = "Employee creates a draft with line items". Every flow must run in the browser and assert the displayed result plus a postcondition read back independently. UC1_E2 as first proposed (amount 0) is blocked by `min="0.01"` before the server is reached, so use currency `123` for UC2_E2. Record the missing edit UI as an observation (not a defect) in `docs/team/issues/ui_no_edit_form.md`. Use getByLabel/getByRole, scope duplicate "Description" labels to the row, tell me before adding any data-testid, run with workers: 1. Flow table: UC1 M submit, A1 three items, A2 draft not submitted, E1 button gone after submit, E2 other employee gets "Request not found"; UC2 M create, A1 add/remove items and total, A2 remove disabled with one item, E1 blank title, E2 currency 123.

## F6. Use cases: checks before pushing
1. Mutation check: temporarily remove `@Pattern` from currency, restart the backend, run the Playwright suite, show UC2_E2 fails, restore, show 10 of 10 pass; save the failing output as `docs/team/evidence/uc/mutation_check_currency.txt`; do not commit the temporary change.
2. Show line counts and first/last lines of run1.txt and run2.txt (complete raw output).
3. Show the final text of UC1_E2_cross_user_access_denied.
4. Show sonar-project.properties, .gitignore, `git status --short`; confirm node_modules and playwright-report are not tracked and Sonar does not scan tests/team/e2e.
5. Write `docs/team/issues/ui_generic_validation_error.md`.

## F7. Use cases: merge master and re-verify
The docs PR #6 is already merged. `git fetch origin`, merge `origin/master` into `member1/use-cases-uc1-uc2` (a merge, not a rebase), keep both sets of entries in any conflicting log files, confirm the PR #6 evidence files exist, rerun the 10 Playwright tests and the team tests with the JaCoCo check, show raw output, then wait.

---------------------------------------------------------------------
## PROMPT 4: consistency, hand-off notes, PDF section, prompt archive
Same hard rules as before (only real tool output, no fabricated or edited evidence, no continue-on-error, my git identity Anfey-SE <i243112@isb.nu.edu.pk>, do not push until I say so). Branch from updated master: member1/final-docs.
1. Consistency check. Read every file in docs/team/ and every evidence file name. List every number that appears in more than one place (team tests, full suite, PIT, JaCoCo scope, Sonar numbers, mutants analysed, path count) with file and line. Report every mismatch. Do not fix silently: show them and ask me, then correct to the REAL value from the raw evidence.
2. Evidence check. For every evidence file referenced from any doc, check it exists. List every referenced PR or run URL in a table (url, what it proves, evidence file).
3. Hand-off notes: update docs/team/05_handoff_notes.md (where CI lives, what each step does, how to run team tests locally for unit, JaCoCo, PIT, how to run the Playwright suite, seeded accounts, reset, Docker needs, branch protection and merge-commit rule, where teammates put tests). Run every command and show raw output; do not write commands you have not run.
4. PDF section: write docs/team/Member1_PDF_Section.md for Member 2. Sections: System and scope; Static analysis; White-box testing; Mutation analysis; CI quality gate (thresholds with justification, blocked PR #3, fix PR #5 with run URLs); Use cases UC1/UC2; Findings (defects and observations); Limitations. Use ONLY facts from the repo docs and raw evidence and cite the evidence file for each number.
5. Prompt archive: create docs/team/prompts/ with the exact prompt files I provide. Update docs/team/ai_use_member1.md so it lists BOTH tools: Antigravity (code, docs, runs) and Claude (chat assistant used to write the Antigravity prompts, review reports and explain concepts), with purpose, what output was used and what I checked or changed. Be honest, do not hide any use.
6. Show a short summary with raw outputs and wait.

---------------------------------------------------------------------
## PROMPT 5: viva drill
Same hard rules. Make a scratch branch viva/drill-scratch that will NEVER be pushed or merged. For each change below, do it on the scratch branch ONE AT A TIME, reset afterwards with git checkout, and report: (a) which team tests fail (exact names, from real output), (b) whether the JaCoCo check, PIT or Sonar step would also fail, (c) the minimal fix. Before running each change write your PREDICTION, then show the real result and say whether the prediction was right.
1. Add a maximum total amount rule (for example reject submit if total > 5000) in ExpenseService.submit.
2. Add a new transition: REJECTED can be resubmitted (RequestStatus and service).
3. Let a FINANCE user also approve at the SUBMITTED stage (assertCanDecide or approverRole).
4. Remove the "not your own request" check (D4) in assertCanDecide.
5. Change the maximum number of line items from 100 to 50 in ExpenseDtos.
Then write docs/team/viva_drill_member1.md: a one-page cheat sheet with, for each rule BR1 to BR4, the test names that cover it, the CI step that blocks a violation, and a 60-second explanation of MC/DC for assertCanDecide. Show raw outputs and wait.
