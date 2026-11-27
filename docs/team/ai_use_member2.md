# AI-Use Record — Member 2 (24i-3097)

| # | Tool | Purpose | Output Summary | What I Checked / Changed |
|---|---|---|---|---|
| 1 | Gemini (Antigravity) | Draft `tests/team/api/openapi.yaml` from Spring Boot controllers & DTOs | OpenAPI 3.0.3 spec covering `/api/auth/*` and `/api/requests/*` | Verified every constraint (`@NotEmpty`, `@Size`, `@Positive`, `@Digits(10,2)`, `@PastOrPresent`) against `ExpenseDtos.java`, `AuthDtos.java`, and `ExpenseController.java`. |
| 2 | Gemini (Antigravity) | Implement `generate_test_data.py` EP + 3-point BVA generator | Python script producing 162 EP and 95 BVA cases in `generated_test_data.json` | Verified 3-point BVA (`below_min`, `at_min`, `above_min`, `below_max`, `at_max`, `above_max`), date `PastOrPresent` boundaries, and regeneration when 2 constraints change. |
| 3 | Gemini (Antigravity) | Draft `tests/team/api/test_expense_api.py` and `tests/team/e2e/test_uc3_uc4_manager_review.py` | Parameterized pytest + requests API suite and Playwright UC3/UC4 suite | Executed all tests against live Docker Compose app (`http://localhost:8081`); adjusted selectors and verified read-back assertions and trail counts. |
| 4 | Gemini (Antigravity) | Draft shared Test Management docs (`07`, `08`, `09`) and `06_use_cases_member2.md` | Test plan, 3-point estimation, RTM, 5×5 risk register, exit criteria, weekly progress & completion report | Cross-checked all metrics against Member 1's actual SonarQube/JaCoCo/PIT outputs (`02_static_analysis.md`, `04_mutation_testing.md`) and our live API/E2E test runs. |
