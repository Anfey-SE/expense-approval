# Defensive Security Assessment — Member 3 (24i-0761)

**Student Name:** Member 3 (Roll No. 24i-0761)  
**Course:** Software Quality Engineering (SE3002) — Section C  
**Target Module:** Expense Requests (Workflow 1: Submit Expense Request, Workflow 2: Review Expense Request)  
**Environment:** Localhost (Backend: `http://localhost:8081`, Frontend: `http://localhost:5173`)  

---

## 1. Routes and Data Mapping

This mapping documents all API endpoints, controllers, data transfer objects (DTOs), and React frontend routes across Workflow 1 (Submit Expense Request) and Workflow 2 (Review Expense Request).

### 1.1 Backend Spring Boot Endpoints & DTOs

| Workflow | HTTP Method | Route Path | Spring Controller Method | Request Body / Parameters | Response DTO & Status | Auth / Role Scope |
|---|---|---|---|---|---|---|
| **Auth** | `POST` | `/api/auth/login` | `AuthController.login()` | `LoginRequest` (`email`, `password`) | `AuthResponse` (JWT, user view, expiration) — `200 OK` | Public |
| **Auth** | `POST` | `/api/auth/register` | `AuthController.register()` | `RegisterRequest` (`email`, `password`, `fullName`, `deptId`) | `AuthResponse` — `201 Created` | Public |
| **Auth** | `GET` | `/api/auth/me` | `AuthController.me()` | None | `UserView` — `200 OK` | Authenticated |
| **W1** | `POST` | `/api/requests` | `ExpenseController.create()` | `CreateRequest` (`title`, `description`, `currency`, `items[]`) | `RequestDetail` — `201 Created` | Authenticated (`EMPLOYEE` / any user with dept) |
| **W1** | `GET` | `/api/requests` | `ExpenseController.list()` | Query: `status`, `page`, `size` | `PageResponse<RequestSummary>` — `200 OK` | Scoped: `EMPLOYEE` (own), `MANAGER` (dept), `FINANCE` (all) |
| **W1** | `GET` | `/api/requests/{id}` | `ExpenseController.get()` | Path: `id` | `RequestDetail` — `200 OK` | Scoped: Owner, Same Dept Manager, Finance |
| **W1** | `PUT` | `/api/requests/{id}` | `ExpenseController.update()` | Path: `id`, Body: `CreateRequest` | `RequestDetail` — `200 OK` | Owner only, `DRAFT` status only |
| **W1** | `POST` | `/api/requests/{id}/submit` | `ExpenseController.submit()` | Path: `id` | `RequestDetail` — `200 OK` | Owner only, transitions `DRAFT -> SUBMITTED` |
| **W2** | `POST` | `/api/requests/{id}/approve` | `ExpenseController.approve()` | Path: `id`, Body: `DecisionInput` (`comment`) | `RequestDetail` — `200 OK` | `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")` |
| **W2** | `POST` | `/api/requests/{id}/reject` | `ExpenseController.reject()` | Path: `id`, Body: `DecisionInput` (`comment`) | `RequestDetail` — `200 OK` | `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")` |

### 1.2 Frontend React SPA Client Routes

| Route Path | React Component | Access Control / Guard | Workflow Context | Primary Actions / Interactivity |
|---|---|---|---|---|
| `/login` | `Login.tsx` | Public | Authentication | Enter email & password, dispatch login, redirect to target or `/` |
| `/` | `RequestList.tsx` | `ProtectedRoute` | Dashboard / Lists | View role-scoped requests, filter by status, navigation to `/requests/new` or `/requests/:id` |
| `/requests/new` | `NewRequest.tsx` | `ProtectedRoute` | Workflow 1 (Draft) | Form entry: title, description, currency, dynamic line items, save draft |
| `/requests/:id` | `RequestDetail.tsx` | `ProtectedRoute` | Workflow 1 & 2 | Inspect request details, line items, and approval trail; submit draft; approve/reject with comment |

---

## 2. Five-Role Access Decision Matrix

The following matrix documents the authorized permissions across all five operational roles based on source code analysis (`ExpenseService.java`, `SecurityConfig.java`, `ExpenseController.java`):

1. **Role 1: Employee Owner** (Alice, Engineering — `alice@acme.com`)
2. **Role 2: Other Employee** (Carol, Sales — `carol@acme.com`)
3. **Role 3: Manager Same Department** (Bob, Engineering Manager — `bob@acme.com`)
4. **Role 4: Manager Other Department** (Dave, Sales Manager — `dave@acme.com`)
5. **Role 5: Finance** (Fiona, Finance Department — `fiona@acme.com`)

| Operation / Endpoint | Target Request State / Condition | Role 1: Employee Owner | Role 2: Other Employee | Role 3: Manager Same Dept | Role 4: Manager Other Dept | Role 5: Finance | Enforcement Mechanism |
|---|---|---|---|---|---|---|---|
| `POST /api/requests` (Create Draft) | N/A | **ALLOW (201)** | **ALLOW (201)** | **ALLOW (201)** | **ALLOW (201)** | **ALLOW (201)** | Authenticated user check |
| `GET /api/requests/{id}` (View Request) | Created by Employee Owner | **ALLOW (200)** | **DENY (404)** | **ALLOW (200)** | **DENY (404)** | **ALLOW (200)** | `ExpenseService.assertCanView` |
| `PUT /api/requests/{id}` (Edit Draft) | Status: `DRAFT` | **ALLOW (200)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | Requester ID check (`ExpenseService:105`) |
| `POST /api/requests/{id}/submit` | Status: `DRAFT` | **ALLOW (200)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | Requester ID check (`ExpenseService:129`) |
| `POST /api/requests/{id}/approve` | Status: `SUBMITTED` | **DENY (403)** | **DENY (403)** | **ALLOW (200)** | **DENY (403)** | **DENY (403)** | PreAuthorize + `assertCanDecide` |
| `POST /api/requests/{id}/approve` | Status: `MANAGER_APPROVED` | **DENY (403)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | **ALLOW (200)** | PreAuthorize + `assertCanDecide` |
| `POST /api/requests/{id}/reject` | Status: `SUBMITTED` | **DENY (403)** | **DENY (403)** | **ALLOW (200)** | **DENY (403)** | **DENY (403)** | PreAuthorize + `assertCanDecide` |
| `POST /api/requests/{id}/reject` | Status: `MANAGER_APPROVED` | **DENY (403)** | **DENY (403)** | **DENY (403)** | **DENY (403)** | **ALLOW (200)** | PreAuthorize + `assertCanDecide` |

> **Note on 404 vs 403 on View:** The application intentionally returns `404 Not Found` rather than `403 Forbidden` when unauthorized users attempt to view requests belonging to other departments (`assertCanView:190-192`), preventing horizontal enumeration and information leakage of request IDs.

---

## 3. Automated Access Verification Test Suite

We verify five key access decisions across roles through both direct API calls and UI browser sessions:

1. **Decision 1 (Allowed):** Manager Same Dept (`bob@acme.com`) approves `SUBMITTED` request -> Status becomes `MANAGER_APPROVED`.
2. **Decision 2 (Denied):** Manager Other Dept (`dave@acme.com`) attempts to approve `SUBMITTED` request -> API returns `403 Forbidden` (`"You can only decide on requests in your own department"`).
3. **Decision 3 (Denied):** Other Employee (`carol@acme.com`) attempts to view & edit Alice's request -> API returns `404 Not Found` for view and `403 Forbidden` for edit; UI displays `"Request not found"` banner.
4. **Decision 4 (Allowed):** Finance (`fiona@acme.com`) approves `MANAGER_APPROVED` request -> Status becomes `FINANCE_APPROVED`.
5. **Decision 5 (Denied):** Employee Owner (`alice@acme.com`) attempts self-approval on own `SUBMITTED` request -> API returns `403 Forbidden` (`"You cannot decide on your own request"`); UI does not render approval controls to requester.

Tests are implemented in [`tests/team/security/access_control.spec.ts`](../../tests/team/security/access_control.spec.ts).

---

## 4. Security Control Reviews

### Review 1: Token & Session Management
- **Observation:** Authentication uses stateless Bearer JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`). Tokens carry user ID, email, role, and department ID in claims. Spring Security is configured with `SessionCreationPolicy.STATELESS` and CSRF protection is disabled (`AbstractHttpConfigurer::disable`) because no stateful session cookies are set.
- **Corroborating Code:**
  - [`SecurityConfig.java:38-40`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/security/SecurityConfig.java#L38-L40): `.csrf(AbstractHttpConfigurer::disable).sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))`
  - [`JwtService.java:44-55`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/security/JwtService.java#L44-L55): JWT creation with HMAC key and 24-hour expiration (`86400s`).
  - [`JwtAuthenticationFilter.java:32-47`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/security/JwtAuthenticationFilter.java#L32-L47): Extracts token from `Authorization: Bearer <token>`, validates signature, and populates `SecurityContextHolder`.
- **Verdict:** **PASS.** Stateless JWT design is properly implemented with clear cryptographic separation. Token expiration is enforced, and malformed tokens return structured `401 UNAUTHORIZED` envelopes.

### Review 2: Multi-Layer Authorization & Role Checks
- **Observation:** Authorization is enforced in two complementary layers:
  1. Declarative method security at the web layer via `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")` on approval and rejection endpoints.
  2. Domain-driven business rule checks inside `ExpenseService` (`assertCanDecide`, `assertCanView`, owner check in `update` and `submit`), preventing role elevation, self-approvals, cross-department approvals, and cross-department enumeration.
- **Corroborating Code:**
  - [`ExpenseController.java:78,87`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/web/ExpenseController.java#L78): `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")`
  - [`ExpenseService.java:166-180`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/service/ExpenseService.java#L166-L180): Checks stage role matching, department equivalence, and explicitly forbids self-decisions (`r.getRequester().getId().equals(me.getUserId())`).
  - [`ExpenseService.java:182-193`](file:///c:/Python%20Projects/expense-approval/src/main/java/com/sandy/expense/service/ExpenseService.java#L182-L193): Restricts read access and conceals request existence from other departments with `404 Not Found`.
- **Verdict:** **PASS.** Robust defense-in-depth authorization. Role-based access control (RBAC) combined with attribute-based access control (ABAC) prevents horizontal and vertical privilege escalation.

---

## 5. OWASP ZAP Passive Scan Results

An OWASP ZAP proxy (`zaproxy/zap-bare:2.17.0`) was deployed in passive inspection mode (zero active attacks, no spiders, purely analyzing live traffic). Playwright executed the complete end-to-end lifecycle of Workflow 1 (Draft -> Submission by Alice) and Workflow 2 (Manager approval by Bob -> Finance approval by Fiona) through `http://localhost:8080`.

- **Total Alerts:** 58
- **High Risk:** 0
- **Medium Risk:** 12
- **Low Risk:** 26
- **Informational:** 20

### Distinct Alert Findings

| Risk Level | Alert Name | Count | CWE ID | Description & Mitigation |
|---|---|---|---|---|
| **Medium** | Missing Anti-clickjacking Header | 6 | CWE-1021 | The response does not include `X-Frame-Options` or CSP `frame-ancestors`. Configure Spring Security and Vite/Nginx headers to include `X-Frame-Options: DENY`. |
| **Medium** | Content Security Policy (CSP) Header Not Set | 6 | CWE-693 | Missing `Content-Security-Policy` header to prevent XSS and unauthorized resource loading. Add a strict CSP header defining `default-src 'self'`. |
| **Low** | X-Content-Type-Options Header Missing | 25 | CWE-693 | Missing `X-Content-Type-Options: nosniff` header on static assets and API envelopes, allowing MIME type sniffing. |
| **Low** | Timestamp Disclosure - Unix | 1 | CWE-497 | Timestamps in Unix epoch or ISO formats disclose internal server clock synchronization. Low risk for internal business applications. |
| **Informational** | Information Disclosure - Suspicious Comments | 8 | CWE-615 | Developer comments or debug indicators present in Vite bundles. |
| **Informational** | Modern Web Application | 6 | CWE--1 | Detected client-side single page application architecture. |
| **Informational** | Authentication / Session Identified | 5 | CWE--1 | Identified login requests and JWT bearer exchanges. |

Full HTML and JSON reports are preserved in:
- HTML Report: [`evidence/m3/zap/zap-report.html`](../../evidence/m3/zap/zap-report.html)
- JSON Report: [`evidence/m3/zap/zap-report.json`](../../evidence/m3/zap/zap-report.json)
- Summary: [`evidence/m3/zap/summary.md`](../../evidence/m3/zap/summary.md)

---

## 6. Dependency Vulnerability Audits Summary

### 6.1 Frontend (`npm audit`)
- **Package Manager:** npm (auditing `frontend/package-lock.json`)
- **Packages Scanned:** 168 dependencies
- **Vulnerabilities Found:** 2 High Severity
  1. **Vite (`vite` <= 6.1.6):** Server-Side Request Forgery (SSRF) and Arbitrary File Read in development server via WebSocket and crafted URLs (GHSA-c647-8m2c-5878, GHSA-9cwx-2883-4wmm).
     - *Impact:* Affects local Vite dev server only; in production Spring Boot serves pre-built static assets.
     - *Correction:* Upgrade `vite` to `>= 6.1.7` or `>= 6.2.0`.
  2. **Source Map JS (`source-map-js` <= 1.2.0):** ReDoS vulnerability in sourcemap parser.
     - *Correction:* Upgrade transitive dependency via `npm update source-map-js`.
- Raw reports: [`evidence/m3/security/npm-audit.json`](../../evidence/m3/security/npm-audit.json) and [`evidence/m3/security/npm-audit.txt`](../../evidence/m3/security/npm-audit.txt).

### 6.2 Backend (`org.owasp:dependency-check-maven:check`)
- **Build Tool:** Maven (auditing `pom.xml` dependencies)
- **Engine:** OWASP Dependency-Check Maven Plugin v13.0.0
- **Execution Result:** Attempted live check against the National Vulnerability Database (NVD 2.0 API).
- **Genuine Barrier Encountered:** NVD 2.0 API requires an official API key (`nvdApiKey`) to avoid rate limit resets and 403 Forbidden throttling during initial CVE data feed downloads. Without an API key configured in the environment, the task threw `NvdApiException: Invalid API Key, length of 0 too short... NoDataException: No data exists in the local database`.
- **Dependency Inventory:** Audited complete compile and runtime classpath (Spring Boot 3.3.4, Spring Security, Spring Data JPA, Hibernate, JJWT 0.12.6, PostgreSQL Driver 42.7.4, Flyway 10.18.0).
- Raw logs & dependency tree: [`evidence/m3/security/dependency-check-log.txt`](../../evidence/m3/security/dependency-check-log.txt) and [`evidence/m3/security/maven-dependencies.txt`](../../evidence/m3/security/maven-dependencies.txt).
