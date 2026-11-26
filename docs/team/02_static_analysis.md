# Task 5 — Static Analysis (SonarQube)

## 1. Tool and Setup

| Field | Value |
|---|---|
| Tool | SonarQube Community Build **26.11.0.134175** |
| Deployment | Local Docker container: `docker run -d --name sonarqube -p 9000:9000 -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community` |
| Scanner | `org.sonarsource.scanner.maven:sonar-maven-plugin:5.9.0.7382` (declared in `pom.xml`) |
| Coverage input | `target/site/jacoco/jacoco.xml` produced by **`./mvnw clean test jacoco:report -Dtest="*WhiteBoxTest"`** (**team tests ONLY — 75 tests, 0 failures; `clean` wipes `target/jacoco.exec` first so JaCoCo's default append mode does not merge in the 32 upstream integration tests**) |
| Project key | `expense-approval` |
| SCM revision analysed | `92e6ed2acfbe5a7b16ead351f3d1de7df2f98984` |
| CE task | `07ae8f77-c571-4640-97c6-7253374e97ec` (status: SUCCESS) |
| Scan command | `mvnw sonar:sonar -Dsonar.host.url=http://localhost:9000 -Dsonar.token=<token> -Dsonar.projectKey=expense-approval -Dsonar.sources=src/main/java -Dsonar.tests=tests/team/unit -Dsonar.java.binaries=target/classes -Dsonar.java.test.binaries=target/test-classes -Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml` |
| Evidence files | `docs/team/evidence/05_sonar_scan.txt`, `docs/team/evidence/05_sonar_measures.txt`, `docs/team/evidence/06_team_only_clean_jacoco.txt`, `docs/team/evidence/06_team_only_clean_jacoco_check.txt`, `docs/team/evidence/06_team_only_clean_jacoco.xml` |

> [!IMPORTANT]
> **Which tests produced the coverage fed to SonarQube?**  
> **Team tests only** (`*WhiteBoxTest`, 75 unit tests across `DomainWhiteBoxTest`, `AuthServiceWhiteBoxTest`, and `ExpenseServiceWhiteBoxTest`), executed after `mvnw clean`. Running `clean` first is essential because JaCoCo's `jacoco.exec` file appends across runs by default; without `clean`, an earlier full 107-test run contaminated `jacoco.xml` (inflating overall Sonar coverage to 84.8% and `ExpenseController` to 70.6%). With a clean team-only run, `ExpenseController` measures **0.0%**, proving the upstream HTTP integration tests were excluded.

---

## 2. Summary Dashboard (Clean Team-Only Coverage)

| Metric | Value | Rating / Gate |
|---|---|---|
| **Quality Gate** | ✅ **OK** | — |
| Bugs | **0** | A (Reliability) |
| Vulnerabilities | **2** | D (Security) |
| Code Smells | **0** | A (Maintainable) |
| Security Hotspots | **0** | — |
| Coverage (overall) | **56.9 %** | — |
| Line Coverage | **55.9 %** | — |
| Branch Coverage | **61.1 %** | — |
| Duplicated Lines | **0.0 %** | — |
| Technical Debt (`sqale_index`) | **0 min** | A (Maintainability) |
| Cyclomatic Complexity (whole project) | **171** | — |
| Cognitive Complexity (whole project) | **53** | — |
| NCLOC | **1 373** | — |

---

## 3. Metric Explanations (Plain English)

### 3.1 Quality Gate — OK ✅

A Quality Gate is a pass/fail policy SonarQube evaluates after each scan.  
In this run the gate uses the default **"Sonar way"** configuration (new-code violations condition).  
Result: **OK** — the project passes the default gate.

> [!NOTE]
> Custom CI quality thresholds (JaCoCo 100% check on the 4 target classes and PIT `mutationThreshold`) are enforced explicitly in Task 7 rather than relying solely on Sonar's default new-code gate.

---

### 3.2 Bugs — 0 (Reliability Rating: A)

A **bug** is code that is likely to behave incorrectly at runtime (e.g., null dereference, resource leak, incorrect API usage).  
SonarQube found **0 bugs** across all 33 main source files, giving Reliability Rating **A**.

---

### 3.3 Vulnerabilities — 2 (Security Rating: D)

A **vulnerability** is a security weakness that could be exploited by an attacker.  
SonarQube found **2 vulnerabilities**, both in upstream `SecurityConfig.java`:

| # | Severity | Rule | Location | Description |
|---|---|---|---|---|
| 1 | **CRITICAL** | `java:S4502` | `SecurityConfig.java:38` | Spring Security CSRF protection is disabled. Without CSRF tokens, a malicious page on another origin can forge requests if cookie-based sessions are used. |
| 2 | **MAJOR** | `java:S5122` | `SecurityConfig.java:117` | CORS is configured with a permissive policy (wildcard origin pattern). |

**Why they exist**: This is a React + JWT SPA. CSRF is disabled because requests authenticate via `Authorization: Bearer <token>` headers rather than cookies, so stateless JWT endpoints are not vulnerable to CSRF. CORS is permissive for local development convenience; production would restrict origins to the deployed frontend domain.  
**Security rating D**: Any project with at least one CRITICAL vulnerability receives a D security rating regardless of context.

> [!IMPORTANT]
> Both vulnerabilities are in upstream production source (`SecurityConfig.java`). No secrets, tokens, or passwords are committed anywhere in the repository: `.sonar-token.txt` and `.sonar/` are listed in `.gitignore`, and `sonar-project.properties` contains no credentials.

---

### 3.4 Code Smells — 0 (Technical Debt: 0 min, Maintainability Rating: A)

A **code smell** is a maintainability issue (long methods, complex nesting, unused locals, etc.). **Technical debt** (`sqale_index`) estimates how many minutes it would take to fix all code smells.  
Result: **0 code smells**, **0 min technical debt**, Maintainability Rating **A**.

---

### 3.5 Security Hotspots — 0

A **security hotspot** flags security-sensitive code needing manual human review (separate from confirmed vulnerabilities).  
Result: **0 hotspots**.

---

### 3.6 Coverage — 56.9 % overall (Line: 55.9 %, Branch: 61.1 %)

SonarQube imports `target/site/jacoco/jacoco.xml` and computes coverage across **all 33 main source classes** (`src/main/java`). Because this scan used **clean team-only unit tests** (`*WhiteBoxTest`), only classes exercised by our unit tests show coverage:

| Scope / Class | Line Coverage | Branch Coverage | Notes |
|---|---|---|---|
| **Whole project (33 classes, JaCoCo XML)** | **55.9 %** (257/460) | **61.1 %** (66/108) | Sonar reports **56.9 %** overall (instruction+branch formula), **55.9 %** line, **61.1 %** branch |
| `ExpenseService` (scoped target) | **100.0 %** (107/107) | **100.0 %** (50/50) | Confirmed in Sonar file measures & JaCoCo XML |
| `AuthService` (scoped target) | **100.0 %** (32/32) | **100.0 %** (4/4) | Confirmed in JaCoCo XML |
| `RequestStatus` (scoped target) | **100.0 %** (14/14) | **100.0 %** (6/6) | Confirmed in JaCoCo XML |
| `ExpenseRequest` (scoped target) | **100.0 %** (9/9) | *n/a (0 branches)* | Confirmed in JaCoCo XML |
| `ExpenseController` (unscoped web controller) | **0.0 %** (0/13) | **0.0 %** (0/4) | **Isolation proof**: HTTP integration tests (`src/test`) were NOT included |

**Why project-wide coverage is 56.9 %**: Our team unit tests cover the 4 scoped service/domain classes at **100 %**, while web controllers (`ExpenseController`, `AuthController`), security filters, JPA repositories, and Spring configuration require the upstream Testcontainers HTTP integration tests (`src/test`) and are therefore at 0 % in a team-only unit run.

---

### 3.7 Duplicated Lines — 0.0 %

**Duplicated lines density** measures the percentage of lines appearing in duplicated code blocks across files.  
Result: **0.0 %** — no duplicated blocks detected.

---

### 3.8 Cyclomatic Complexity & Cognitive Complexity

- **Cyclomatic Complexity (`complexity`)**: **171** across the whole project (103 functions in 42 classes). Counts independent control-flow paths (`if`, `else if`, loops, `case`, `catch`, `&&`, `||`, `?:`).
- **Cognitive Complexity (`cognitive_complexity`)**: **53** across the whole project. Weights nested control structures higher than flat guard clauses so it reflects human readability effort.

#### File-Level Measures for `ExpenseService.java` (Real Sonar Output)

SonarQube Community Build **does not expose per-method complexity** in either the UI or the REST API (`api/measures/component_tree` beneath a `FIL` component returns `0` child components). It reports aggregates at **file (`FIL`) level** only:

| Component | Cyclomatic Complexity | Cognitive Complexity | Functions | NCLOC |
|---|---|---|---|---|
| Whole project (`expense-approval`) | **171** | **53** | 103 | 1 373 |
| `ExpenseService.java` (file total) | **45** | **22** | 14 | 181 |
| `ExpenseController.java` (file total) | **10** | **2** | 8 | 80 |

For our target method `ExpenseService.assertCanDecide` (lines 166–180 of `ExpenseService.java`), the hand-computed McCabe cyclomatic complexity is **V(G) = 6** (`1 + 4 ifs + 1 && = 6`; see [03_mcdc_and_cfg.md](03_mcdc_and_cfg.md)). Why is Sonar's whole-file cognitive complexity (**22**) less than half its cyclomatic complexity (**45**) across `ExpenseService.java`'s 14 methods? Because methods like `assertCanDecide` use flat early-exit `throw` guards (`if (...) throw ...;`) with zero nesting depth, avoiding cognitive nesting penalties, and `switch` expressions / simple getters contribute to cyclomatic complexity more heavily than cognitive complexity.

---

## 4. Files Analysed & Ratings Summary

- **Indexed files**: 33 main Java files (`src/main/java`), 3 team white-box test files (`tests/team/unit`).
- **Ratings**: Reliability **A** (0 bugs), Security **D** (2 upstream vulnerabilities in `SecurityConfig.java`), Maintainability **A** (0 code smells, 0 min debt).

---

## 5. Run Command (Reproducible)

```bash
# 1. Start SonarQube (one-time, needs Docker)
docker run -d --name sonarqube -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community

# 2. Wait ~90 seconds for startup, then generate a token at http://localhost:9000

# 3. Run team tests ONLY with clean target/ (prevents jacoco.exec append contamination)
./mvnw clean test jacoco:report -Dtest="*WhiteBoxTest"

# 4. Verify the 4 scoped classes pass JaCoCo 100% check
./mvnw jacoco:check

# 5. Run Sonar scan
./mvnw sonar:sonar \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=<YOUR_TOKEN> \
  -Dsonar.projectKey=expense-approval \
  -Dsonar.sources=src/main/java \
  -Dsonar.tests=tests/team/unit \
  -Dsonar.java.binaries=target/classes \
  -Dsonar.java.test.binaries=target/test-classes \
  -Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml
```

Results are at: `http://localhost:9000/dashboard?id=expense-approval`
