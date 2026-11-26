# JaCoCo Coverage Scope & Uncovered Code Justification

All coverage figures below are taken verbatim from [`docs/team/evidence/06_team_only_clean_jacoco.xml`](evidence/06_team_only_clean_jacoco.xml) (clean team-only `*WhiteBoxTest` run). Overall bundle totals in that evidence file: **LINE 257/460 (55.9%)**, **BRANCH 66/108 (61.1%)**.

## 1. Per-Class Classification (`src/main/java` — 30 classes)

| Class (`com.sandy.expense.*`) | Category | Line Coverage | Branch Coverage | In 100% Scope? | Justification |
|---|---|---|---|---|---|
| `service.ExpenseService` | Server-side business logic | 107/107 (100.0%) | 50/50 (100.0%) | **Yes** (L+B) | Core reimbursement workflow, authorization guards (BR1–BR4), and state transitions. |
| `service.AuthService` | Server-side business logic | 32/32 (100.0%) | 4/4 (100.0%) | **Yes** (L+B) | Registration, duplicate-email guard, department lookup, and login authentication rules. |
| `domain.RequestStatus` | Server-side business logic | 14/14 (100.0%) | 6/6 (100.0%) | **Yes** (L+B) | State machine enum defining `approverRole()` and `onApprove()` transitions. |
| `domain.ExpenseRequest` | Server-side business logic | 9/9 (100.0%) | 0/0 (N/A) | **Yes** (Line) | Domain aggregate root (`addItem`, `recomputeTotal`). |
| `domain.ApprovalAction` | Server-side business logic | 4/4 (100.0%) | 0/0 (N/A) | No (trivial enum) | 3-constant enum (`SUBMIT`, `APPROVE`, `REJECT`); 100% covered incidentally. |
| `domain.Role` | Server-side business logic | 4/4 (100.0%) | 0/0 (N/A) | No (trivial enum) | 3-constant enum (`EMPLOYEE`, `MANAGER`, `FINANCE`); 100% covered incidentally. |
| `domain.Department` | Infrastructure (JPA entity) | 3/3 (100.0%) | 0/0 (N/A) | No | JPA entity with simple getters/setters; no business rules. |
| `domain.Approval` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `domain.ExpenseItem` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `domain.User` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `repo.ApprovalRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `repo.DepartmentRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `repo.ExpenseRequestRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; queries verified in Postgres integration tests. |
| `repo.UserRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `web.AuthController` | Thin controller | 0/6 (0.0%) | 0/0 (N/A) | No | Delegates directly to `AuthService`; covered by HTTP integration tests (`src/test/`). |
| `web.DepartmentController` | Thin controller | 0/6 (0.0%) | 0/0 (N/A) | No | Read-only repository list endpoint; covered by HTTP integration tests. |
| `web.ExpenseController` | Thin controller | 0/13 (0.0%) | 0/4 (0.0%) | No | Thin HTTP wrapper delegating to `ExpenseService`; covered by HTTP integration tests and Member 2 API tests. |
| `web.SpaController` | Thin controller | 0/2 (0.0%) | 0/0 (N/A) | No | Forwards SPA routes to `index.html`; routing/presentation only. |
| `web.dto.AuthDtos` | DTO | 0/0 (N/A) | 0/0 (N/A) | No | Java records and validation annotations only. |
| `web.dto.ExpenseDtos` | DTO | 0/0 (N/A) | 0/0 (N/A) | No | Java records + Jakarta Bean Validation; all constraints tested in `ExpenseDtosValidationWhiteBoxTest` (46 tests). |
| `web.dto.PageResponse` | DTO | 7/7 (100.0%) | 0/0 (N/A) | No | Generic pagination record wrapper; 100% covered incidentally. |
| `web.error.ApiException` | Infrastructure | 10/10 (100.0%) | 0/0 (N/A) | No | Exception factory methods; 100% covered incidentally. |
| `web.error.GlobalExceptionHandler` | Infrastructure | 0/31 (0.0%) | 0/2 (0.0%) | No | Spring `@RestControllerAdvice` mapping exceptions to HTTP JSON; verified in HTTP integration tests. |
| `ExpenseApprovalApplication` | Configuration / Bootstrap | 0/20 (0.0%) | 0/16 (0.0%) | No | Spring Boot `main()` and CORS bean setup; framework bootstrap. |
| `config.DataSeeder` | Configuration | 0/24 (0.0%) | 0/2 (0.0%) | No | Startup `CommandLineRunner` seeding demo users/departments; excluded in `sonar-project.properties`. |
| `security.SecurityConfig` | Configuration (contains HTTP auth rules) | 0/39 (0.0%) | 0/0 (N/A) | No *(note below)* | Spring Security filter chain & URL authorization rules; requires full Spring web context (covered by `src/test/`). |
| `security.JwtService` | Infrastructure (contains token rules) | 1/28 (3.6%) | 0/8 (0.0%) | No *(note below)* | Issues/parses HS256 JWTs and enforces `APP_JWT_SECRET >= 32` bytes + TTL; covered by `src/test/` integration tests. |
| `security.JwtAuthenticationFilter` | Infrastructure | 0/20 (0.0%) | 0/10 (0.0%) | No | Servlet `OncePerRequestFilter` extracting `Bearer` token; covered by `src/test/` HTTP tests. |
| `security.AppUserDetailsService` | Infrastructure | 0/6 (0.0%) | 0/0 (N/A) | No | Spring Security `UserDetailsService` adapter around `UserRepository`. |
| `security.AppUserPrincipal` | Infrastructure (authority adapter) | 16/23 (69.6%) | 2/2 (100.0%) | No *(note below)* | Adapts `User` to `UserDetails` (`ROLE_` authority prefix); remaining `UserDetails` getters exercised by Spring Security in `src/test/`. |

## 2. Transparency Note on Security / JWT Classes

Three security classes contain rule-like behaviour outside `service/` and `domain/`:
- **`SecurityConfig`**: defines HTTP route access rules (`/api/auth/**` permitAll, `/api/requests/**` authenticated).
- **`JwtService`**: enforces minimum 32-byte HS256 secret length, embeds `role` and `dept` claims, and validates token expiry.
- **`AppUserPrincipal`**: prefixes `ROLE_` onto `Role` for `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")`.

These are **not** in the unit-level JaCoCo 100% gate because they operate at the Spring Security / HTTP filter boundary; they are verified in the upstream `src/test/java/com/sandy/expense/integration/` suite (run in CI as part of the 157-test full suite).
