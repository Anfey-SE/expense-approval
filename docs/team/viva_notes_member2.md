# Viva Preparation Notes — Member 2 (24i-3097)

## 1. Owned Core Area
- **OpenAPI Specification:** `tests/team/api/openapi.yaml`
- **Automated Test Data Generator:** `tests/team/api/generate_test_data.py` -> `tests/team/api/generated_test_data.json` (162 EP + 95 3-point BVA cases)
- **API & Integration Suite:** `tests/team/api/test_expense_api.py` (pytest + requests)
- **Own Use Cases:** UC3 & UC4 (`docs/team/06_use_cases_member2.md` + `tests/team/e2e/test_uc3_uc4_manager_review.py`)
- **Shared Test Management:** Test plan, estimation, RTM (`07`), Risk register & exit criteria (`08`), Monitoring & completion report (`09`)

## 2. Commands to Rerun Selected Tests in Viva
```powershell
# 1. Start the app (if not already running)
docker compose up -d

# 2. Regenerate EP & 3-point BVA test data from openapi.yaml
python tests/team/api/generate_test_data.py

# 3. Run Member 2 API & Integration tests
pytest tests/team/api/test_expense_api.py -v

# 4. Run Member 2 Playwright E2E tests (UC3 & UC4)
pytest tests/team/e2e/test_uc3_uc4_manager_review.py -v
```

## 3. Live Task Readiness (Updated OpenAPI Spec)
If the examiner changes a constraint in `tests/team/api/openapi.yaml` (e.g., `title.maxLength`, `items.maxItems`, `amount.maximum`, or `comment.maxLength`):
1. Edit the constraint in `tests/team/api/openapi.yaml`.
2. Re-run `python tests/team/api/generate_test_data.py`.
3. Show the updated `at_max` / `above_max` values in `tests/team/api/generated_test_data.json`.
4. Re-run `pytest tests/team/api/test_expense_api.py -k "create_request or decision_input" -v`:
   - If the spec was tightened below the backend DTO limit (e.g., `title.maxLength: 100` while backend allows `200`), the `above_max` test (`len=101`) expects `400` per spec but the backend returns `201`, demonstrating spec-vs-implementation drift!
   - If the spec was loosened above the backend DTO limit (e.g., `title.maxLength: 250`), the `at_max` test (`len=250`) expects `201` per spec but the backend returns `400`.
