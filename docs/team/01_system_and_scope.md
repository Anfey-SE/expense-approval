# Task 1 & 3 — System Description, Installation, and Scope

## 1. Project Identity

| Field | Value |
|---|---|
| Upstream repository | https://github.com/LijuanTang94/expense-approval |
| Our fork | https://github.com/Anfey-SE/expense-approval |
| Baseline commit | `ae596c382e61685841696a63efff094359aa4e59` |
| Licence | MIT (see `LICENSE` in repo root) |
| Stack | Java 21 · Spring Boot 4.1 · PostgreSQL + Flyway · Spring Security + JWT (jjwt 0.12.6) · React 19 + Vite + TypeScript |

## 2. Installation and Start-up Commands

All commands verified on Windows 11, Java 21.0.13.1 (Eclipse Temurin), Docker 29.8.1.

```bash
# 1. Start the database (PostgreSQL 16-alpine via Testcontainers-managed compose)
docker compose up -d db

# 2. Start the backend (Spring Boot dev server on port 8080 by default)
./mvnw spring-boot:run

# 3. Start the React frontend (port 5173 by default)
cd frontend
npm install && npm run dev
```

Seeding is **automatic**: `DataSeeder.java` (`src/main/java/com/sandy/expense/config/DataSeeder.java`) uses a `@Bean CommandLineRunner` to insert departments and demo accounts at startup if they are absent.

```bash
# Reset to a clean slate (stops and removes all containers and volumes)
docker compose down -v

# Run all tests (team + upstream integration) — requires Docker 29+ workaround
./mvnw test
# Docker 29+ workaround (see README): pin Testcontainers API version
./mvnw test -DargLine="-Dapi.version=1.44"

# Run only team white-box unit tests (no Docker required)
./mvnw test -Dtest="*WhiteBoxTest"
```

## 3. Database

**Technology**: PostgreSQL 16, schema owned by **Flyway** migrations.  
`spring.jpa.hibernate.ddl-auto=validate` — Hibernate may **only** verify that entities match the schema; it may never mutate it.

Migrations:
- `V1__init_schema.sql` — 5 tables: `departments`, `users`, `expense_requests`, `expense_items`, `approvals`.
- `V2__optimistic_locking_and_fixes.sql` — adds the `version` column (optimistic lock) and fixes `timestamptz`/`text`/`char` type mismatches that failed `validate`.

**Schema key facts** (from `src/main/resources/db/migration/V1__init_schema.sql`):

```sql
-- line 25
CONSTRAINT chk_users_role CHECK (role IN ('EMPLOYEE', 'MANAGER', 'FINANCE'))

-- line 47-49
CONSTRAINT chk_req_status CHECK (
    status IN ('DRAFT', 'SUBMITTED', 'MANAGER_APPROVED', 'FINANCE_APPROVED', 'REJECTED')
)

-- line 50
CONSTRAINT chk_req_total_nonneg CHECK (total_amount >= 0)

-- line 66
CONSTRAINT chk_item_amount_pos CHECK (amount > 0)
```

## 4. Roles and Enforcement

Three roles defined in `Role.java` (`src/main/java/com/sandy/expense/domain/Role.java`): `EMPLOYEE`, `MANAGER`, `FINANCE`.

**Two-layer defence**:

1. **HTTP layer** — `@PreAuthorize` on controller methods  
   Source: `src/main/java/com/sandy/expense/web/ExpenseController.java` lines 78 and 87:
   ```java
   @PreAuthorize("hasAnyRole('MANAGER','FINANCE')")  // approve endpoint, line 78
   @PreAuthorize("hasAnyRole('MANAGER','FINANCE')")  // reject endpoint, line 87
   ```
   Spring Security evaluates these before service code runs; an EMPLOYEE hitting these endpoints receives HTTP 403 immediately.

2. **Service layer** — fine-grained checks inside `ExpenseService.assertCanDecide` and `assertCanView`  
   Source: `src/main/java/com/sandy/expense/service/ExpenseService.java` lines 166–193:
   - Role must own the stage (`me.getRole() != needed` → 403).
   - For MANAGER: department must match (`!r.getDepartment().getId().equals(me.getDepartmentId())` → 403).
   - Self-decision forbidden (`r.getRequester().getId().equals(me.getUserId())` → 403).
   - Cross-department reads return 404 not 403 (leaking existence is prevented by `assertCanView`).

3. **Registration lock** — `AuthService.register` always assigns `Role.EMPLOYEE` regardless of request payload (line 61):
   ```java
   // line 59-61
   // Role is NOT taken from the request: self-registration always yields an EMPLOYEE.
   // Promotion to MANAGER/FINANCE is an administrative action, never self-service.
   u.setRole(Role.EMPLOYEE);
   ```

4. **JWT carries role** — `AppUserPrincipal` reconstructed from token claims on every request (`AppUserPrincipal.java` lines 32–39), no per-request DB hit for identity.

## 5. Requirements (extracted from real code and README)

### Authentication workflow

**REQ-A1 — Email uniqueness**  
Source: `AuthService.java` line 45–46:
```java
if (users.existsByEmail(req.email())) {
    throw ApiException.conflict("EMAIL_TAKEN", "That email is already registered");
}
```
Duplicate email registration returns HTTP 409 with code `EMAIL_TAKEN`.

**REQ-A2 — Self-registration always yields EMPLOYEE**  
Source: `AuthService.java` lines 59–61 (verbatim above). Role is never taken from the request body.

**REQ-A3 — Department assignment is optional at registration**  
Source: `AuthService.java` lines 48–54:
```java
Department dept = null;
if (req.departmentId() != null) {
    dept =
            departments
                    .findById(req.departmentId())
                    .orElseThrow(() -> ApiException.badRequest("BAD_DEPARTMENT", "Unknown department"));
}
```
Department FK is validated if supplied; `null` is accepted.

**REQ-A4 — Failed login returns 401, never issues a token**  
Source: `AuthService.java` lines 72–74:
```java
} catch (BadCredentialsException e) {
    throw new ApiException(
            org.springframework.http.HttpStatus.UNAUTHORIZED, "BAD_CREDENTIALS", "Invalid email or password");
}
```

### Expense request workflow

**REQ-E1 — A request requires at least 1 line item and at most 100**  
Source: `ExpenseDtos.java` lines 41–43:
```java
@NotEmpty(message = "at least one line item is required")
        @Size(max = 100, message = "a request cannot have more than 100 line items")
        @Valid
        List<ItemInput> items) {}
```

**REQ-E2 — Item amount must be positive with at most 2 decimal places**  
Source: `ExpenseDtos.java` lines 31–34:
```java
@NotNull
        @Positive
        @Digits(integer = 10, fraction = 2, message = "amount supports at most 2 decimal places")
        BigDecimal amount,
```

**REQ-E3 — Item date cannot be in the future**  
Source: `ExpenseDtos.java` line 35:
```java
@NotNull @PastOrPresent(message = "expense date cannot be in the future") LocalDate incurredOn) {}
```

**REQ-E4 — Currency defaults to USD; supplied values are upper-cased; blank input is treated as absent**  
Source: `ExpenseService.java` line 52:
```java
r.setCurrency(input.currency() == null || input.currency().isBlank() ? "USD" : input.currency().toUpperCase());
```

**REQ-E5 — Only the requester may submit their own draft**  
Source: `ExpenseService.java` lines 129–131:
```java
if (!r.getRequester().getId().equals(me.getUserId())) {
    throw ApiException.forbidden("You can only submit your own requests");
}
```

**REQ-E6 — Only DRAFT requests can be submitted**  
Source: `ExpenseService.java` lines 132–134:
```java
if (r.getStatus() != RequestStatus.DRAFT) {
    throw ApiException.conflict("NOT_SUBMITTABLE", "Only DRAFT requests can be submitted");
}
```

**REQ-E7 — A request with no line items cannot be submitted (service-level guard)**  
Source: `ExpenseService.java` lines 135–137:
```java
if (r.getItems().isEmpty()) {
    throw ApiException.badRequest("EMPTY_REQUEST", "Add at least one line item before submitting");
}
```
Note: this branch is unreachable via HTTP (REQ-E1 fires first at the web layer), but is reachable at the service boundary directly.

**REQ-E8 — Concurrent approvals are rejected; second writer receives HTTP 409**  
Source: `ExpenseRequest.java` lines 46–48:
```java
@Version
@Column(nullable = false)
private long version;
```
`GlobalExceptionHandler` maps `OptimisticLockingFailureException` to HTTP 409. Documented in README: *"a version column makes the second commit fail … mapped to 409 Conflict"*.

### Approval workflow

**REQ-AP1 — Only MANAGER or FINANCE may call the approve/reject endpoints**  
Source: `ExpenseController.java` lines 78, 87:
```java
@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")
```

**REQ-AP2 — The role that owns the stage is determined by the request's current status**  
Source: `RequestStatus.java` lines 21–27:
```java
public Role approverRole() {
    return switch (this) {
        case SUBMITTED -> Role.MANAGER;
        case MANAGER_APPROVED -> Role.FINANCE;
        default -> null;
    };
}
```

**REQ-AP3 — MANAGER must be in the same department as the request**  
Source: `ExpenseService.java` line 174:
```java
if (needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())) {
    throw ApiException.forbidden("You can only decide on requests in your own department");
}
```

**REQ-AP4 — Nobody may decide on their own request**  
Source: `ExpenseService.java` lines 177–179:
```java
if (r.getRequester().getId().equals(me.getUserId())) {
    throw ApiException.forbidden("You cannot decide on your own request");
}
```

## 6. Business Rules with File and Method References

### BR1 — Submit requires ≥ 1 line item

| Layer | File | Method / Line | Enforcement |
|---|---|---|---|
| Web (DTO) | `web/dto/ExpenseDtos.java:41` | `CreateRequest` record | `@NotEmpty` triggers HTTP 400 before service is called |
| Service | `service/ExpenseService.java:135–137` | `submit(AppUserPrincipal, Long)` | `EMPTY_REQUEST` guard for direct callers |

The DTO also caps items at 100 (`@Size(max=100)`, line 42) and validates each item (`@Valid`, line 43).

### BR2 — Manager decision: role + department + not-self (assertCanDecide)

| Layer | File | Method / Line | Condition |
|---|---|---|---|
| Web | `web/ExpenseController.java:78,87` | `approve`, `reject` | `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")` — employees blocked at HTTP layer |
| Service | `service/ExpenseService.java:166–180` | `assertCanDecide` | D1: stage awaits nobody → `NOT_PENDING`; D2: role mismatch → 403; D3: MANAGER + wrong dept → 403; D4: self-decision → 403 |

### BR3 — State machine: transitions encoded in RequestStatus

| Layer | File | Method / Lines | Rule |
|---|---|---|---|
| Enum | `domain/RequestStatus.java:21–36` | `approverRole()`, `onApprove()` | Single source of truth for who may act and what happens |
| Service | `service/ExpenseService.java:146–157` | `approve`, `reject` | Reads `r.getStatus().onApprove()` and passes result to `transition()` |
| Persistence | `V1__init_schema.sql:47–49` | DB CHECK constraint | Rejects any value outside the 5 allowed statuses at the DB layer |

REJECTED is reachable from SUBMITTED (`reject`, line 156) and from MANAGER_APPROVED (`reject`, same line) — the same call path, differentiated only by the request's current status.

### BR4 — Finance acts only on MANAGER_APPROVED

This is an emergent property of BR2 + BR3: `MANAGER_APPROVED.approverRole()` returns `Role.FINANCE` (line 24 of `RequestStatus.java`), so D2 of `assertCanDecide` rejects any other role, and D1 rejects FINANCE trying to act on SUBMITTED (which needs MANAGER, not FINANCE).

| File | Lines | Explanation |
|---|---|---|
| `domain/RequestStatus.java` | 23–24 | `SUBMITTED → Role.MANAGER`, `MANAGER_APPROVED → Role.FINANCE` |
| `service/ExpenseService.java` | 171–173 | `if (me.getRole() != needed)` — FINANCE on SUBMITTED fails here |

