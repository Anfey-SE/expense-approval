# JaCoCo Coverage Scope & Uncovered Code Justification

Measured on branch `member1/final-checks` (with `SecurityWhiteBoxTest` and updated `pom.xml` JaCoCo gate, parent commit `6b1d3bd`) via:

```powershell
.\mvnw.cmd clean test jacoco:report jacoco:check "-Dtest=*WhiteBoxTest" --no-transfer-progress
```

- **Tests run**: **136** (`DomainWhiteBoxTest`: 15, `SecurityWhiteBoxTest`: 11, `AuthServiceWhiteBoxTest`: 11, `ExpenseServiceWhiteBoxTest`: 53, `ExpenseDtosValidationWhiteBoxTest`: 46), 0 failures, 0 errors.
- **Bundle totals**: **LINE 292/460 (63.5%)**, **BRANCH 74/108 (68.5%)**.

## 1. Per-Class Classification (`src/main/java` — 30 classes)

| Class (`com.sandy.expense.*`) | Category | Line Coverage | Branch Coverage | In 100% Scope? | Justification |
|---|---|---|---|---|---|
| `service.ExpenseService` | Server-side business logic | 107/107 (100.0%) | 50/50 (100.0%) | **Yes** (L+B) | Core reimbursement workflow, authorization guards (BR1–BR4), and state transitions. |
| `service.AuthService` | Server-side business logic | 32/32 (100.0%) | 4/4 (100.0%) | **Yes** (L+B) | Registration, duplicate-email guard, department lookup, and login authentication rules. |
| `domain.RequestStatus` | Server-side business logic | 14/14 (100.0%) | 6/6 (100.0%) | **Yes** (L+B) | State machine enum defining `approverRole()` and `onApprove()` transitions. |
| `domain.ExpenseRequest` | Server-side business logic | 9/9 (100.0%) | 0/0 (N/A) | **Yes** (Line) | Domain aggregate root (`addItem`, `recomputeTotal`). |
| `security.JwtService` | Security / token rules | 28/28 (100.0%) | 8/8 (100.0%) | **Yes** (L+B) | Enforces `APP_JWT_SECRET >= 32` bytes, token TTL, claim embedding (`sub`, `email`, `role`, `dept`), and signature/expiry verification. |
| `security.AppUserPrincipal` | Security / authority mapping | 23/23 (100.0%) | 2/2 (100.0%) | **Yes** (L+B) | Maps `Role` to `ROLE_*` `GrantedAuthority`, maps nullable `departmentId`, and implements `UserDetails` flags. |
| `domain.ApprovalAction` | Server-side business logic | 4/4 (100.0%) | 0/0 (N/A) | No (trivial enum) | 3-constant enum (`SUBMIT`, `APPROVE`, `REJECT`); 100% covered incidentally. |
| `domain.Role` | Server-side business logic | 4/4 (100.0%) | 0/0 (N/A) | No (trivial enum) | 3-constant enum (`EMPLOYEE`, `MANAGER`, `FINANCE`); 100% covered incidentally. |
| `domain.Department` | Infrastructure (JPA entity) | 3/3 (100.0%) | 0/0 (N/A) | No | JPA entity with simple getters/setters; no business rules. |
| `domain.Approval` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `domain.ExpenseItem` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `domain.User` | Infrastructure (JPA entity) | 0/0 (N/A) | 0/0 (N/A) | No | Lombok/JPA entity with no custom methods. |
| `repo.ApprovalRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `repo.DepartmentRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `repo.ExpenseRequestRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; Spring Data generates queries at runtime. |
| `repo.UserRepository` | Infrastructure (Spring Data) | 0/0 (N/A) | 0/0 (N/A) | No | Spring Data JPA interface; no implementation code. |
| `web.AuthController` | Thin controller | 0/6 (0.0%) | 0/0 (N/A) | No | Thin HTTP endpoint delegating directly to `AuthService`; no business rules. |
| `web.DepartmentController` | Thin controller | 0/6 (0.0%) | 0/0 (N/A) | No | Read-only repository list endpoint; no business rules. |
| `web.ExpenseController` | Thin controller | 0/13 (0.0%) | 0/4 (0.0%) | No | Thin HTTP wrapper delegating to `ExpenseService` (plus `page`/`size` clamping). |
| `web.SpaController` | Thin controller | 0/2 (0.0%) | 0/0 (N/A) | No | Forwards SPA routes to `index.html`; routing/presentation only. |
| `web.dto.AuthDtos` | DTO | 0/0 (N/A) | 0/0 (N/A) | No | Java records and validation annotations only. |
| `web.dto.ExpenseDtos` | DTO | 0/0 (N/A) | 0/0 (N/A) | No | Java records + Jakarta Bean Validation; all constraints tested in `ExpenseDtosValidationWhiteBoxTest` (46 tests). |
| `web.dto.PageResponse` | DTO | 7/7 (100.0%) | 0/0 (N/A) | No | Generic pagination record wrapper; 100% covered incidentally. |
| `web.error.ApiException` | Infrastructure | 10/10 (100.0%) | 0/0 (N/A) | No | Exception factory methods; 100% covered incidentally. |
| `web.error.GlobalExceptionHandler` | Infrastructure | 0/31 (0.0%) | 0/2 (0.0%) | No | Spring `@RestControllerAdvice` mapping exceptions to HTTP JSON envelopes. |
| `ExpenseApprovalApplication` | Configuration / Bootstrap | 0/20 (0.0%) | 0/16 (0.0%) | No | Spring Boot `main()` and CORS bean setup; framework bootstrap. |
| `config.DataSeeder` | Configuration | 0/24 (0.0%) | 0/2 (0.0%) | No | Startup `CommandLineRunner` seeding demo users/departments; excluded in `sonar-project.properties`. |
| `security.SecurityConfig` | Configuration | 0/39 (0.0%) | 0/0 (N/A) | No | Configuration class defining the Spring Security filter chain; exercised indirectly by the Playwright use-case tests. |
| `security.JwtAuthenticationFilter` | Infrastructure | 0/20 (0.0%) | 0/10 (0.0%) | No | Servlet `OncePerRequestFilter` extracting `Bearer` headers and populating `SecurityContextHolder`. |
| `security.AppUserDetailsService` | Infrastructure | 0/6 (0.0%) | 0/0 (N/A) | No | Spring Security `UserDetailsService` adapter around `UserRepository`. |
