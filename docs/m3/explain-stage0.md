# Stage 0 Explanation: Setup and Discovery — Member 3 (24i-0761)

## 1. What Was Done
1. **Branch & Git Identity Verification:** Confirmed that the current Git branch is `member3/usability-security-performance-uc5-uc6`, committed user is `uswa-shafiq-505` (`u.s.w.a.shafiq.202922@gmail.com`), and git commit history contains Member 2's merged pull requests (`#12` and `#13`).
2. **Repository & Architecture Discovery:** Analyzed `README.md`, `pom.xml`, `docker-compose.yml`, Spring Boot configurations (`application.yml`), Flyway database migrations (`V1__init_schema.sql`), and the React 19 frontend (`frontend/src/`).
3. **Environment and Tool Verification:** Checked system architecture, OS, CPU cores, RAM, and verified versions of Java 21, Maven wrapper (`.\mvnw.cmd`), Node.js (`v24.19.0`), npm (`11.17.0`), Docker (`29.8.0`), and k6 (`v2.2.0`).
4. **Folder Structure & Tracking Files Initialized:** Created deliverables directories `tests/team/a11y`, `tests/team/security`, `tests/team/perf`, `evidence/m3`, `docs/m3`, and initialized `docs/m3/effort-log.md` (with placeholder `HOURS: to be filled by me`), `docs/m3/ai-use-record.md`, `docs/m3/prompts.md`, `docs/m3/defect-notes.md`, and `docs/m3/environment.md`.
5. **Dependency Installation:** Installed frontend dependencies via `npm install` in `frontend/`, installed E2E testing dependencies (`@playwright/test`, `@axe-core/playwright`, `playwright-lighthouse`, `lighthouse`) in `tests/team/e2e/`, and installed the Playwright Chromium browser.

---

## 2. Why Each Step Was Done
- **Branch and Git Identity Verification:** In collaborative Git projects, ensuring that you are on your designated branch (`member3/...`) and that your git author matches your identity prevents accidental commits to `master` and maintains a clear audit trail of each team member's contributions.
- **Environment & Tool Checks:** Different tools often have subtle version requirements (e.g., Spring Boot 4.1 requires Java 21 LTS; Playwright requires matched browser binaries). Catching misconfigurations early (such as locating Java 21 at `C:\Program Files\Eclipse Adoptium\jdk-21.0.13.10002-hotspot` and pointing `JAVA_HOME` to it) avoids cryptic runtime compilation or execution failures later.
- **Dependency Isolation & Structure Setup:** Placing all Member 3 files under `tests/team/<area>/`, `evidence/m3/`, and `docs/m3/` prevents conflicts with Member 1's unit/mutation tests and Member 2's API tests, adhering to the team convention.
- **Honest Defect & Effort Tracking:** In software quality engineering, fabricated metrics invalidate the entire testing lifecycle. Tracking only genuine observations and letting the human author record their real effort hours ensures academic and professional integrity.

---

## 3. What Each Tool Output Means
- **`java -version` (`21.0.13.1 LTS`):** Indicates the Eclipse Temurin OpenJDK runtime is installed. The Spring Boot backend leverages Java 21 language features (switch pattern matching, records).
- **`.\mvnw.cmd -version` (`Apache Maven 3.9.16`):** The Maven Wrapper ensures that everyone on the team builds the project with the exact same Maven version without requiring a manual system-wide Maven install.
- **`node -v` (`v24.19.0`) & `npm -v` (`11.17.0`):** The Node runtime and package manager required to bundle the Vite/React frontend and run the Playwright/Axe/Lighthouse test suites.
- **`docker ps` / `com.docker.service`:** Docker is used to run PostgreSQL 16 on port 5433 for dev/test databases and to run OWASP ZAP in passive proxy mode. If `docker ps` outputs `failed to connect to the docker API at npipe://...`, it indicates the Docker Desktop desktop app is currently stopped and needs to be launched.
- **`k6 version` (`v2.2.0`):** A modern open-source performance testing tool written in Go that runs JavaScript-based load test scripts against REST APIs.
- **`npx playwright --version` (`Version 1.65.1`):** A browser automation framework capable of running headless Chromium for end-to-end user journey tests and accessibility scans.

---

## 4. Five Likely Viva Questions with Short Answers

### Q1: What is the role of `JAVA_HOME` and why did the backend require Java 21?
**Answer:** `JAVA_HOME` is an environment variable pointing to the root directory of the Java Development Kit (JDK). Spring Boot 4.1.0 and the project's `pom.xml` target Java 21 bytecode; without Java 21 installed and configured in `JAVA_HOME`, Maven cannot compile modern Java features like record classes and pattern matching for switch.

### Q2: Why does this project use Flyway rather than letting Hibernate auto-generate the database schema (`ddl-auto=update`)?
**Answer:** In production software, `ddl-auto=update` is dangerous because Hibernate may drop columns or alter schemas unpredictably. Flyway uses versioned, immutable SQL migration scripts (`V1__init_schema.sql`, `V2...`) as the single source of truth. With `ddl-auto=validate`, Hibernate only checks that JPA entity mappings match the database; it never mutates the schema.

### Q3: What are the three roles in Expense Approval MIS and what are their exact boundaries?
**Answer:** 
1. `EMPLOYEE`: Can only create drafts and view/submit their own expense requests.
2. `MANAGER`: Can view requests within their own department and approve/reject requests in the `SUBMITTED` stage (cannot approve their own requests).
3. `FINANCE`: Can view all requests organisation-wide and provide final approval or rejection for requests in the `MANAGER_APPROVED` stage.

### Q4: Why is the backend stateless with JWT rather than using HTTP sessions?
**Answer:** Stateless JWT tokens embed user identity, role, and department directly into the cryptographic claims (`sub`, `role`, `dept`). The server's JWT filter validates the token signature on each request without querying the database for session state, allowing horizontal scaling and eliminating session-affinity requirements.

### Q5: What is the purpose of the Maven Wrapper (`mvnw.cmd`) and npm lockfiles (`package-lock.json`)?
**Answer:** Both enforce build reproducibility. `mvnw.cmd` downloads and executes a pinned Maven version (3.9.16), while `package-lock.json` pins exact dependency and transitive dependency versions, ensuring that tests run identically across every developer's machine and CI runners.
