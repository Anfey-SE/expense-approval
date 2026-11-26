# Tool & Dependency Versions (Member 1)

Every version below was read directly from local command output, `pom.xml`, or `.github/workflows/ci.yml`.

## 1. Local CLI & Runtime Tools

| Tool | Version | Source |
|---|---|---|
| Java (`java -version`) | `openjdk version "21.0.13.1" 2026-11-17 LTS` (Eclipse Temurin `21.0.13.1+2-LTS`) | `java -version` |
| Maven Wrapper (`.\mvnw.cmd -v`) | `Apache Maven 3.9.16` | `.\mvnw.cmd -v` |
| Node.js (`node -v`) | `v24.19.0` | `node -v` |
| npm (`npm -v`) | `11.17.0` | `npm -v` |
| Docker (`docker --version`) | `Docker version 29.9.3, build 5457199` | `docker --version` |
| Playwright (`npx playwright --version`) | `Version 1.65.1` (`@playwright/test` `^1.52.0` in `tests/team/e2e/package.json`) | `npx playwright --version` |

## 2. Build, Analysis & CI Versions (`pom.xml`, `.github/workflows/ci.yml`)

| Tool / Component | Version | Source |
|---|---|---|
| Spring Boot parent | `4.1.0` | `pom.xml` L8 |
| `jacoco-maven-plugin` | `0.8.12` | `pom.xml` L170 |
| `pitest-maven` | `1.30.2` | `pom.xml` L285 |
| `pitest-junit5-plugin` | `1.2.3` | `pom.xml` L290 |
| `sonar-maven-plugin` | `5.9.0.7382` | `pom.xml` L280 |
| `build-helper-maven-plugin` | `3.6.0` | `pom.xml` L151 |
| `maven-surefire-plugin` | `3.5.6` (inherited from Spring Boot `4.1.0`) | `mvnw` output |
| GitHub Actions runner | `ubuntu-latest` | `.github/workflows/ci.yml` L12 |
| SonarQube Server | Community Build `26.11.0.134175` (`sonarqube:community@sha256:7b2296713a92b8ea0dd7a083a25faadc59376c9a1e6daf2744a89711c54ea1ba`) | `.github/workflows/ci.yml` L51, L57 & `docs/team/evidence/05_sonar_measures.txt` L1 |
