# Environment Details — Member 3 (24i-0761)

Every detail below was directly read and executed in the local Windows environment.

## 1. Operating System & Hardware

| Parameter | Value | Source |
|---|---|---|
| OS Name & Architecture | Windows 11 (`Windows_NT`, `amd64`) | `$env:OS`, `$env:PROCESSOR_ARCHITECTURE` |
| Processor (CPU) | Intel64 Family 6 Model 140 Stepping 1, GenuineIntel (8 Logical Processors) | `$env:PROCESSOR_IDENTIFIER`, `$env:NUMBER_OF_PROCESSORS` |
| Working Directory | `c:\Python Projects\expense-approval` | Local repository root |
| Git Branch | `member3/usability-security-performance-uc5-uc6` | `git branch --show-current` |
| App Commit Hash (Baseline) | `ef5eb1903367e3ec62254322ea2596e0a79219b3` | `git rev-parse HEAD` (includes PR #12 and #13 from Member 2) |
| Git Config User | `uswa-shafiq-505` (`u.s.w.a.shafiq.202922@gmail.com`) | `git config user.name`, `git config user.email` |

## 2. Tool & Runtime Versions

| Tool | Version | Executable / Path | Verification Command | Status |
|---|---|---|---|---|
| Java | `openjdk version "21.0.13.1" 2026-11-17 LTS` | `C:\Program Files\Eclipse Adoptium\jdk-21.0.13.10002-hotspot` | `java -version` | Installed & Verified (requires `JAVA_HOME`) |
| Maven Wrapper | `Apache Maven 3.9.16` | `.\mvnw.cmd` | `.\mvnw.cmd -version` | Installed & Verified |
| Node.js | `v24.19.0` | Node binary in PATH | `node -v` | Installed & Verified |
| npm | `11.17.0` | npm binary in PATH | `npm -v` | Installed & Verified |
| Docker CLI | `Docker version 29.8.0, build 88096ef` | Docker CLI in PATH | `docker -v` | Installed |
| Docker Desktop Engine | Docker Desktop 29.8.0 (`com.docker.service`) | `C:\Program Files\Docker\Docker\Docker Desktop.exe` | `docker ps` | Engine stopped; needs Desktop UI launched |
| k6 | `k6.exe v2.2.0 (commit/00a9a1b7f5, go1.26.5)` | k6 in PATH | `k6 version` | Installed & Verified |
| Playwright Chromium | `Chrome for Testing 159.0.8154.6` (Playwright v1255) | `ms-playwright\chromium-1255` | `npx playwright install chromium` | Installed & Verified (exit code 0) |
| System Chrome | `158.0.8127.37` | `C:\Program Files\Google\Chrome\Application\chrome.exe` | File VersionInfo | Installed |
| Axe-core | `@axe-core/playwright` | `tests/team/e2e/node_modules` | npm package | Configured |
| Lighthouse | `lighthouse`, `playwright-lighthouse` | `tests/team/e2e/node_modules` | npm package | Configured |
| OWASP ZAP | Docker image `zaproxy/zap-stable` | Docker | `docker pull zaproxy/zap-stable` | Requires Docker daemon |

## 3. Application Endpoints & Ports

- **Backend:** `http://localhost:8081` (Spring Boot 4.1.0)
- **Frontend:** `http://localhost:5173` (React 19 + Vite + TypeScript)
- **Database:** PostgreSQL 16 on port `5433` (`docker compose up -d db`)
