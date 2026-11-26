# Team Hand-Off Notes (Member 1 — 24i-3112)

## 1. Where CI Lives & What Each Step Does

The CI workflow lives at [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) (`SQE Quality Gate CI`, triggered on every `pull_request`, job `quality-gate` on `ubuntu-latest`, timeout 45 min):

1. **Checkout & JDK 21**: `actions/checkout@v4` (`fetch-depth: 0` for Sonar) and Temurin JDK 21 with Maven cache.
2. **Build and install custom PIT mutators**: `./mvnw -f tools/pit-custom-mutators/pom.xml clean install --no-transfer-progress`
3. **Run team tests with JaCoCo report and 100 % check**: `./mvnw clean test jacoco:report jacoco:check -Dtest="*WhiteBoxTest" --no-transfer-progress` (team-only coverage in `target/site/jacoco/jacoco.xml`; enforces 100% line/branch on `ExpenseService`, `AuthService`, `RequestStatus`, `JwtService`, `AppUserPrincipal`, and 100% line on `ExpenseRequest`).
4. **Run full test suite (upstream + team, JaCoCo skipped)**: `./mvnw test -Djacoco.skip=true --no-transfer-progress` (runs all 168 tests = 136 team + 32 upstream integration tests using Testcontainers).
5. **Start SonarQube 26.11.0 container**: Starts `sonarqube:community` (digest `7b22967...`) on port `9000` and polls `/api/system/status` until `UP`.
6. **Create custom quality gate and set as default**: Creates `SQE-CI` with overall-code conditions (`bugs > 0`, `vulnerabilities > 2`, `code_smells > 0`, `coverage < 50`, `duplicated_lines_density > 3`).
7. **Run SonarQube scan and enforce quality gate**: Generates a one-time token and runs `./mvnw sonar:sonar -Psonar -Dsonar.host.url=http://localhost:9000 -Dsonar.token="$TOKEN" -Dsonar.qualitygate.wait=true`.
8. **Run PIT mutation testing (threshold 95 %)**: `./mvnw test-compile org.pitest:pitest-maven:mutationCoverage -DmutationThreshold=95 --no-transfer-progress`.
9. **Upload JaCoCo and PIT reports**: Uploads `target/site/jacoco/` and `target/pit-reports/` as artifact `quality-reports` (`if: always()`).

---

## 2. Running Team Tests Locally (Unit, JaCoCo, PIT)

*(On Windows PowerShell, use `.\mvnw.cmd` with `JAVA_HOME` pointing to JDK 21. On Linux/macOS, use `./mvnw`.)*

### Unit tests + JaCoCo 100% check (no Docker needed)
```powershell
.\mvnw.cmd clean test jacoco:report jacoco:check "-Dtest=*WhiteBoxTest" --no-transfer-progress
```

### Full suite (136 team + 32 upstream Testcontainers tests — **requires Docker**; *not run* in this docs pass)
```powershell
.\mvnw.cmd test -Djacoco.skip=true --no-transfer-progress
```
Note: `pom.xml` passes `-Dapi.version=1.44` to Surefire for Docker 29+ compatibility with Testcontainers.

### PIT Mutation Testing (from a fresh Maven cache)
```powershell
.\mvnw.cmd -f tools/pit-custom-mutators/pom.xml clean install --no-transfer-progress
.\mvnw.cmd test-compile org.pitest:pitest-maven:mutationCoverage "-DmutationThreshold=95" --no-transfer-progress
```

---

## 3. Running the Playwright E2E Suite (`tests/team/e2e`)

1. Start PostgreSQL + Spring Boot backend on `:8081` (e.g. `docker compose up -d db` [*not run*], then `.\mvnw.cmd spring-boot:run`) and Vite frontend on `:5173` (`cd frontend && npm run dev` [*not run* — app was already running]).
2. Install Playwright and Chromium (first time only) and run with `workers: 1`:
```powershell
cd tests\team\e2e
npm install
npx playwright install chromium
npx playwright test
```
*(Playwright is configured with `workers: 1` in [`playwright.config.ts`](../../tests/team/e2e/playwright.config.ts) and is **not** wired into `quality-gate` in `ci.yml`.)*

---

## 4. Seeded Accounts, Reset & Docker Requirements

### Seeded Demo Accounts (`DataSeeder.java`)
All accounts use password **`password123`**:

| Email | Name | Role | Department |
|---|---|---|---|
| `alice@acme.com` | Alice Employee | `EMPLOYEE` | Engineering |
| `bob@acme.com` | Bob Manager | `MANAGER` | Engineering |
| `carol@acme.com` | Carol Employee | `EMPLOYEE` | Sales |
| `dave@acme.com` | Dave Manager | `MANAGER` | Sales |
| `fiona@acme.com` | Fiona Finance | `FINANCE` | Finance |

### Resetting the Database *(command not run)*
```bash
docker compose down -v && docker compose up -d
```
`DataSeeder` runs automatically on first boot when `users.count() == 0`.

### Docker Requirements
- **Needed for**: PostgreSQL (`docker-compose.yml`, port `5433`), upstream Testcontainers integration tests (`mvnw test`), and local SonarQube scans.
- **Not needed for**: `*WhiteBoxTest` unit tests, JaCoCo check, PIT mutation testing, or running Playwright once the app is already up.

---

## 5. Branch Protection, Merge-Commit Rule & Where to Put Tests

- **Branch protection**: Pull requests to `master` require the `quality-gate` CI check to pass. Merge using **merge commits** (not squash/rebase) so PR commits and history stay intact.
- **Where teammates should put their work**:
  - Java white-box / unit tests: `tests/team/unit/...` (name classes `*WhiteBoxTest` so `-Dtest="*WhiteBoxTest"` and PIT pick them up automatically).
  - Playwright E2E tests: `tests/team/e2e/tests/`.
  - Team docs, issue drafts, and evidence: `docs/team/`, `docs/team/issues/`, `docs/team/evidence/`.
