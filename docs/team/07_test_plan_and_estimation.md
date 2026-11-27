# Test Plan, Three-Point Estimation, and Traceability Matrix

**Project:** Expense Approval MIS (`https://github.com/Anfey-SE/expense-approval`, baseline `ae596c3`)  
**Prepared by:** Member 2 (24i-3097) — Shared Test Management Lead  
**Group:** 24i-3112 (M1), 24i-3097 (M2), 24i-0761 (M3)

---

## 1. Test Plan

### 1.1 Scope
- **In Scope:**
  - **Module:** Expense Requests (`ExpenseController`, `ExpenseService`, `ExpenseRequest`, `RequestStatus`, `ExpenseDtos`) and supporting Authentication (`AuthController`, `AuthService`, `SecurityConfig`).
  - **Workflow 1 (Submit Expense Request):** Create draft with line items (`POST /api/requests`), update draft (`PUT /api/requests/{id}`), submit (`POST /api/requests/{id}/submit`).
  - **Workflow 2 (Review Expense Request):** Manager approve/reject (`POST /api/requests/{id}/approve`, `/reject`), Finance approve/reject, read-back (`GET /api/requests/{id}`, `GET /api/requests`).
  - **Quality Dimensions:** Static analysis (SonarQube), White-box unit & MC/DC + Mutation (PIT), OpenAPI-driven EP/BVA API & integration testing, Browser E2E (UC1–UC6), Usability & Accessibility (Lighthouse + axe-core), Defensive Security (OWASP ZAP + Dependency-Check/npm audit), Performance & Recovery (k6 + failure-recovery).
- **Out of Scope:**
  - Upstream tests in `src/test/` (earn 0 marks; kept separate from `tests/team/`).
  - Administrative user/department management UI (no admin endpoints exist in the application).

### 1.2 Test Approach by Risk Level
| Risk Score (L × I) | Risk Tier | Testing Technique & Depth |
|---|---|---|
| **15 – 25** | Critical / High | 100% statement + branch coverage + MC/DC + custom PIT mutators; exhaustive EP + 3-point BVA API tests; E2E Playwright happy/exception flows; security role-matrix & k6 load verification. |
| **8 – 14** | Medium | Standard EP + BVA API tests; SonarQube static analysis; passive ZAP scan; Lighthouse/axe-core accessibility audits. |
| **1 – 7** | Low | Smoke / sanity checks and exploratory verification. |

### 1.3 Roles & Responsibilities
| Member | Roll No. | Core Area | Shared Items | Own Use Cases |
|---|---|---|---|---|
| Member 1 | 24i-3112 | Static analysis, white-box unit, PIT mutation, CI quality gate | System & Scope | UC1, UC2 (Submit) |
| Member 2 | 24i-3097 | OpenAPI spec, EP/BVA test data generator, API & integration tests | Test plan, estimation, traceability, risk register, exit criteria, monitoring & completion report | UC3, UC4 (Manager Review) |
| Member 3 | 24i-0761 | Usability/accessibility, defensive security, performance & recovery | Defect management & RCA | UC5, UC6 (Finance Review) |

### 1.4 Test Environment & Test Data
- **Backend:** Java 21, Spring Boot 4.1, PostgreSQL 16 (Docker `postgres:16-alpine` on host port `5433`), Flyway (`V1`, `V2`).
- **Frontend:** React 19 + Vite + TypeScript served via Spring Boot on `http://localhost:8081` (Docker Compose) or `http://localhost:5173` (dev).
- **Seeded Synthetic Accounts (`DataSeeder.java`, password `password123`):**
  - `alice@acme.com` (`EMPLOYEE`, Engineering), `bob@acme.com` (`MANAGER`, Engineering)
  - `carol@acme.com` (`EMPLOYEE`, Sales), `dave@acme.com` (`MANAGER`, Sales)
  - `fiona@acme.com` (`FINANCE`, Finance)
- **Reset Procedure:** `docker compose down -v && docker compose up -d` wipes volumes and re-seeds cleanly.
- **Generated API Test Data:** `tests/team/api/generated_test_data.json` produced by `generate_test_data.py` from `openapi.yaml`.

### 1.5 Schedule (5-Week Plan)
| Phase | Planned Work | Owners |
|---|---|---|
| Days 1–5 | Repo confirmation, local run, requirements/rules/roles, baseline commit, Google Sheet registration | M1 leads, All |
| Week 2 | Test plan, risk register, OpenAPI spec (M2); SonarQube + CI skeleton (M1); Playwright setup (M3) | M1, M2, M3 |
| Weeks 2–3 | Write UC1–UC6 specifications | All |
| Weeks 3–4 | Unit + MC/DC (M1); Generator + API tests (M2); A11y/Security/Perf (M3); E2E UC1–UC6 (All) | M1, M2, M3 |
| Week 5 | Mutation + CI gate & blocked PR (M1); Spec regeneration demo (M2); A11y fix & retest (M3) | M1, M2, M3 |
| Final Week | Completion report & release decision (M2); RCA & Pareto (M3); Final zip/PDF & viva prep (All) | All |

### 1.6 Entry, Exit, Suspension, and Resumption Criteria
- **Entry Criteria:** Baseline commit runs locally via Docker Compose; `DataSeeder` populates all 5 demo accounts; OpenAPI spec and unit test harness compile cleanly.
- **Exit Criteria:** Defined quantitatively in [`08_risk_register_and_exit_criteria.md`](08_risk_register_and_exit_criteria.md) (100% business-logic branch coverage & PIT gate, 100% API/E2E requirement coverage with 0 open Critical/High defects, p95 <= 500 ms with < 1% unexpected errors, and 0 critical accessibility/security findings).
- **Suspension Criteria:** Docker/DB container fails to boot, CI runner outage > 24h, or a blocking defect prevents authentication (`POST /api/auth/login` returning 500).
- **Resumption Criteria:** Environment restored (`docker compose up -d`), blocking defect fixed and verified on a clean build.

---

## 2. Three-Point Effort Estimation vs. Actual Effort

Formula: **Expected Effort $E = \frac{O + 4M + P}{6}$** (hours), **Std Dev $SD = \frac{P - O}{6}$**.

| Area / Activity | Owner | Optimistic ($O$) | Most Likely ($M$) | Pessimistic ($P$) | Expected ($E$) | Actual Effort (h) | Variance (Actual − $E$) |
|---|---|---|---|---|---|---|---|
| System & Scope + Baseline | M1 | 4.0 | 6.0 | 10.0 | 6.33 | 6.50 | +0.17 |
| Static Analysis (SonarQube + CFG) | M1 | 3.0 | 5.0 | 8.0 | 5.17 | 5.50 | +0.33 |
| White-Box Unit Tests + MC/DC | M1 | 8.0 | 12.0 | 18.0 | 12.33 | 13.00 | +0.67 |
| PIT Mutation + Custom Mutators + CI | M1 | 6.0 | 9.0 | 14.0 | 9.33 | 10.00 | +0.67 |
| OpenAPI Spec + EP/BVA Generator + Demo | M2 | 5.0 | 7.0 | 11.0 | 7.33 | 7.00 | −0.33 |
| API & Integration Tests (pytest) | M2 | 6.0 | 8.0 | 12.0 | 8.33 | 8.00 | −0.33 |
| Test Plan, Risk, Monitoring, Completion | M2 | 6.0 | 8.0 | 12.0 | 8.33 | 8.50 | +0.17 |
| E2E Use Cases (UC1–UC6, 2 each) | All | 9.0 | 12.0 | 18.0 | 12.50 | 12.00 | −0.50 |
| Usability & Accessibility (LH + axe) | M3 | 5.0 | 7.0 | 11.0 | 7.33 | — (in progress) | — |
| Security & Performance (ZAP + k6) | M3 | 7.0 | 10.0 | 15.0 | 10.33 | — (in progress) | — |
| Defect Management & RCA | M3 | 3.0 | 5.0 | 8.0 | 5.17 | — (in progress) | — |
| **Total (M1 + M2 completed areas)** | **M1+M2** | **47.0** | **65.0** | **99.0** | **66.98** | **67.50 (M1+M2)** | **+0.52** |

---

## 3. Requirements Traceability Matrix (RTM)

All 16 functional requirements (`REQ-A1..A4`, `REQ-E1..E8`, `REQ-AP1..AP4`) and 4 business rules (`BR1..BR4`) from [`01_system_and_scope.md`](01_system_and_scope.md) are traced below.

| Req / Rule ID | Description | Unit Test (M1) | API Test (M2) | E2E Use Case | Status |
|---|---|---|---|---|---|
| **REQ-A1** | Email uniqueness (409 `EMAIL_TAKEN`) | `AuthServiceWhiteBoxTest` | `test_expense_api.py` (auth) | — | Covered |
| **REQ-A2** | Self-registration always yields `EMPLOYEE` | `AuthServiceWhiteBoxTest` | OpenAPI `RegisterRequest` | — | Covered |
| **REQ-A3** | Optional department at registration | `AuthServiceWhiteBoxTest` | — | — | Covered |
| **REQ-A4** | Failed login returns 401 | `AuthServiceWhiteBoxTest` | `test_unauthenticated_requests_rejected` | Login | Covered |
| **REQ-E1 / BR1** | Items count 1..100 (`@NotEmpty`, `@Size(max=100)`) | `ExpenseServiceWhiteBoxTest` | `test_create_request_ep_and_bva` (items BVA) | UC1, UC2 | Covered |
| **REQ-E2** | Item amount > 0, max 2 decimals | `ExpenseServiceWhiteBoxTest` | `test_item_input_ep_and_bva` (amount EP/BVA) | UC2 | Covered |
| **REQ-E3** | Item date `@PastOrPresent` | `ExpenseServiceWhiteBoxTest` | `test_item_input_ep_and_bva` (incurredOn BVA) | UC1 | Covered |
| **REQ-E4** | Currency defaults to `USD`, uppercased | `ExpenseServiceWhiteBoxTest` | `test_create_request_ep_and_bva` + `test_full_happy_path` | UC1 | Covered |
| **REQ-E5** | Only requester may submit own draft | `ExpenseServiceWhiteBoxTest` | `test_disallowed_state_transitions_from_every_state` | UC1-EF | Covered |
| **REQ-E6 / BR3** | Only `DRAFT` can be submitted; valid state machine | `DomainWhiteBoxTest`, `ExpenseServiceWhiteBoxTest` | `test_disallowed_state_transitions_from_every_state`, `test_repeated_requests_no_duplicate_trail_rows` | UC1, UC3, UC4 | Covered |
| **REQ-E7 / BR1** | Empty items guard at service boundary | `ExpenseServiceWhiteBoxTest` | `test_create_request_ep_and_bva` (`items:below_min`) | UC1-EF | Covered |
| **REQ-E8** | Optimistic locking (`@Version`) -> 409 | `ExpenseServiceWhiteBoxTest` | Concurrency / state check | M3 Recovery | Covered |
| **REQ-AP1** | Only `MANAGER`/`FINANCE` call approve/reject | `ExpenseServiceWhiteBoxTest` | `test_br2_and_br4_authorization_rejections` | UC3, UC4, UC5, UC6 | Covered |
| **REQ-AP2 / BR4** | Stage role determined by status (`SUBMITTED`->Manager, `MANAGER_APPROVED`->Finance) | `DomainWhiteBoxTest` | `test_full_happy_path`, `test_br2_and_br4_authorization_rejections` | UC3–UC6 | Covered |
| **REQ-AP3 / BR2** | Manager must be in same department | `ExpenseServiceWhiteBoxTest` (MC/DC) | `test_br2_and_br4_authorization_rejections` | UC3-EF1 | Covered |
| **REQ-AP4 / BR2** | Nobody may decide on own request | `ExpenseServiceWhiteBoxTest` (MC/DC) | `test_br2_and_br4_authorization_rejections` | UC3-EF2 | Covered |

**Requirements Coverage:** 16 / 16 functional requirements (**100%**) and 4 / 4 business rules (**100%**) traced to automated tests.
