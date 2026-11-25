# Task 5 — Static Analysis (SonarQube)

## 1. Tool and Setup

| Field | Value |
|---|---|
| Tool | SonarQube Community Build **26.11.0.134175** |
| Deployment | Local Docker container: `docker run -d --name sonarqube -p 9000:9000 -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community` |
| Scanner | `org.sonarsource.scanner.maven:sonar-maven-plugin:5.9.0.7382` (declared in `pom.xml`) |
| Coverage input | `target/site/jacoco/jacoco.xml` produced by `mvnw test jacoco:report -Dtest="*WhiteBoxTest"` (team tests only) |
| Project key | `expense-approval` |
| SCM revision analysed | `ad2eb05548049dbeb928e436c7038206ec451b8f` |
| CE task | `b21c523b-e43b-42a6-981c-8c67ecb20dea` (status: SUCCESS) |
| Scan command | `mvnw sonar:sonar -Dsonar.host.url=http://localhost:9000 -Dsonar.token=<token> -Dsonar.projectKey=expense-approval -Dsonar.sources=src/main/java -Dsonar.tests=tests/team/unit -Dsonar.java.binaries=target/classes -Dsonar.java.test.binaries=target/test-classes -Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml` |
| Evidence files | `docs/team/evidence/05_sonar_scan.txt`, `docs/team/evidence/05_sonar_measures.txt` |

---

## 2. Summary Dashboard

| Metric | Value | Rating / Gate |
|---|---|---|
| **Quality Gate** | ✅ **OK** | — |
| Bugs | **0** | A (Reliable) |
| Vulnerabilities | **2** | D (Security) |
| Code Smells | **0** | A (Maintainable) |
| Security Hotspots | **0** | — |
| Coverage (overall) | **84.8 %** | — |
| Line Coverage | **87.0 %** | — |
| Branch Coverage | **75.0 %** | — |
| Duplicated Lines | **0.0 %** | — |
| Technical Debt | **0 min** | A (Maintainable) |
| Cyclomatic Complexity | **171** | — |
| Cognitive Complexity | **53** | — |
| NCLOC | **1 373** | — |

---

## 3. Metric Explanations (Plain English)

### 3.1 Quality Gate — OK ✅

A Quality Gate is a pass/fail threshold that SonarQube evaluates after every scan.  
In this run the gate is set to the default **"Sonar way"** profile with **no additional custom conditions**.  
Result: **OK** — the project passes the gate as configured.

> [!NOTE]
> The gate would need custom thresholds (e.g., coverage ≥ 80%, zero new vulnerabilities) to be meaningful for CI blocking. Those are added in Task 7.

---

### 3.2 Bugs — 0

A **bug** is code that is likely to behave incorrectly at runtime (null dereference, resource leak, incorrect API use).  
SonarQube found **zero bugs** across all 33 source files.  
*Plain English*: the code has no known logic errors that Sonar's static rules can detect.

---

### 3.3 Vulnerabilities — 2 (Rating: D)

A **vulnerability** is a security weakness that could be exploited by an attacker.  
SonarQube found **2 vulnerabilities**, both in `SecurityConfig.java`:

| # | Severity | Rule | Location | Description |
|---|---|---|---|---|
| 1 | **CRITICAL** | `java:S4502` | `SecurityConfig.java:38` | Spring Security CSRF protection is disabled (`http.csrf().disable()`). Without CSRF tokens, a malicious page on another origin can forge requests on behalf of a logged-in user. |
| 2 | **MAJOR** | `java:S5122` | `SecurityConfig.java:117` | CORS is configured with a permissive policy (allows all origins via `addAllowedOriginPattern("*")`). This can allow any website to make authenticated cross-origin requests. |

**Why they exist**: This is a React + JWT SPA. CSRF is disabled because the app uses `Authorization: Bearer <token>` headers (not cookies) — stateless JWT is not vulnerable to CSRF. CORS is wide open for development convenience.  
**Are they real risks here?** CSRF disable is safe given JWT Bearer usage. CORS is a development-only risk; production would restrict to the frontend origin.  
**Security rating D**: Even one vulnerability of CRITICAL severity produces a D rating regardless of the justification. The rating reflects what Sonar sees, not the full context.

> [!IMPORTANT]
> These vulnerabilities are in production source code, not in test code. They are upstream design choices, not introduced by the team. No changes are made to production source under the hard rules.

---

### 3.4 Code Smells — 0 (Technical Debt: 0 min, Rating: A)

A **code smell** is a maintainability issue — not a bug, but code that is harder to read, extend, or change safely (long methods, magic numbers, duplicate code blocks, etc.).  
**Zero code smells** means no maintainability issues were flagged.  
**Technical debt** is the estimated time it would take to fix all code smells. Zero smells → zero debt → **Rating A**.

---

### 3.5 Security Hotspots — 0

A **security hotspot** is a security-sensitive section of code that needs human review (e.g., use of `Random` instead of `SecureRandom`, or `eval()`). Unlike vulnerabilities, hotspots are not automatically classified as bugs — a developer must review and mark them safe or as a real issue.  
Result: **0 hotspots** — no security-sensitive patterns found beyond the two vulnerabilities already reported.

---

### 3.6 Coverage — 84.8 % overall (Line: 87.0 %, Branch: 75.0 %)

**What SonarQube counts**: SonarQube imports the JaCoCo XML and reports coverage over all 33 source classes (including controllers, config, DTOs, repositories — not just the 4 scoped classes).

| Dimension | Value | Explanation |
|---|---|---|
| Line coverage | 87.0 % | 87 % of executable lines were executed by team tests |
| Branch coverage | 75.0 % | 75 % of if/switch branches were taken by team tests |
| Overall coverage | 84.8 % | Weighted average of instruction-level hits |

**Why below 100%**: The team's white-box tests target only 4 classes (`ExpenseService`, `AuthService`, `RequestStatus`, `ExpenseRequest`) with 100% coverage on those. The remaining 29 classes (controllers, config, DTOs, Flyway migrations, JPA entities, security filters) are covered only partially or not at all because they require integration tests (HTTP layer, database, JWT filter chain) that are outside the team's scope.

**The 4 scoped classes**: 100% line and branch from team tests alone (verified in Task 2 — see `docs/team/evidence/03_team_tests_only_jacoco_check.txt`).

---

### 3.7 Duplicated Lines — 0.0 %

**Duplication** is detected when a block of ≥ 10 identical lines appears in more than one place.  
Result: **0.0 %** — no duplicated blocks. The codebase has clean separation of concerns with no copy-pasted code.

---

### 3.8 Cyclomatic Complexity — 171 (whole project)

**Cyclomatic complexity** (McCabe, 1976) counts the number of independent paths through a function.  
The whole-project total is **171** across 103 functions in 42 classes (average ≈ 1.66 per function).

**Our target method `assertCanDecide`**: SonarQube computes cyclomatic complexity using the same formula as McCabe's closed-graph method. For `assertCanDecide` (4 `if` statements, 5 independent paths):  
- Our hand calculation (decisions+1): **V(G) = 5**  
- SonarQube cyclomatic: **5** (consistent with our analysis in Task 4)

> [!NOTE]
> SonarQube cyclomatic complexity counts each `if`, `else if`, `for`, `while`, `case`, `catch`, `&&`, `||` and ternary `?:` as +1. For `assertCanDecide` with 4 `if` statements and no compound boolean operators reported by Sonar (the `&&` on line 174 is counted as +1 on the compound condition node), it matches V(G)=5.

---

### 3.9 Cognitive Complexity — 53 (whole project)

**Cognitive complexity** (SonarSource, 2017) measures how hard the code is to *understand*, not just how many paths it has. It penalises nesting more heavily than cyclomatic complexity.  
Whole-project total: **53**.

**Difference from cyclomatic**: Cyclomatic complexity counts all decision nodes equally. Cognitive complexity adds a nesting penalty: a deeply-nested `if` costs more than a flat one. For `assertCanDecide`, which has 4 flat `if` guards with no nesting, SonarQube reports cognitive complexity = **4** (one per `if`, no nesting penalty), while cyclomatic = **5** (decisions+1). This is the typical pattern: flat sequential guards have cognitive ≤ cyclomatic.

---

## 4. Files Analysed

| Count | Description |
|---|---|
| 33 main source files | `src/main/java/**/*.java` |
| 3 test source files | `tests/team/unit/**/*WhiteBoxTest.java` |
| 1 JaCoCo XML report | `target/site/jacoco/jacoco.xml` |

---

## 5. Ratings Summary

| Axis | Rating | Meaning |
|---|---|---|
| Reliability (`sqale_rating`) | **A** | No bugs |
| Security | **D** | ≥ 1 critical vulnerability |
| Maintainability | **A** | No code smells, 0 min debt |

The Security D rating is caused entirely by the two CSRF/CORS issues in the upstream `SecurityConfig.java`. Both are documented upstream design choices for a JWT + React SPA in development mode, not newly introduced issues.

---

## 6. Run Command (Reproducible)

```bash
# 1. Start SonarQube (one-time, needs Docker)
docker run -d --name sonarqube -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community

# 2. Wait ~90 seconds for startup, then generate a token at http://localhost:9000

# 3. Run team tests + JaCoCo report
./mvnw test jacoco:report -Dtest="*WhiteBoxTest"

# 4. Run Sonar scan
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
