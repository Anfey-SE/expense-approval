# Issue #06: Operational Pipeline Defect — OWASP Dependency-Check Maven Build Plugin Fails Due to Unauthenticated NVD 2.0 API Limits

- **Title:** OWASP Dependency-Check Maven Build Target Terminates with Invalid API Key Exception on Clean CI Run
- **Category:** Build & CI Pipeline / Security Automation
- **Severity:** Low / Operational
- **Priority:** Low (P3)
- **Status:** Open (Documented with Environment Setup Guidance)
- **Triage Decision:** Configure repository secret `NVD_API_KEY` in GitHub Actions CI workflow and local development docs.
- **Linked Risk Register ID:** **PJ-01** (*Docker / Build Pipeline failure*, Score: 16)
- **Evidence Link:** [`evidence/m3/security/dependency-check-log.txt`](../../evidence/m3/security/dependency-check-log.txt)

---

## Description & Operational Impact
When invoking `mvn org.owasp:dependency-check-maven:check`, the plugin attempts to sync vulnerability feeds from the NIST National Vulnerability Database (NVD) via their 2.0 REST API. Without an official `nvdApiKey` parameter provided, NIST's endpoint rejects unauthenticated synchronization batches with HTTP 403 or 429 rate limit resets, causing the Maven build to terminate with `NvdApiException: Invalid API Key... NoDataException: No data exists in the local database`.

## Steps to Reproduce
1. In a clean workspace without a cached `.dependency-check` database, run:
   ```powershell
   .\mvnw.cmd org.owasp:dependency-check-maven:check
   ```
2. Observe Maven error: `Failed to execute goal org.owasp:dependency-check-maven:13.0.0:check... NoDataException`.

## Expected vs Actual
- **Expected:** Automated security scans complete cleanly or fall back to cached vulnerability feeds without blocking developer builds.
- **Actual:** Clean builds without an explicit NVD key fail immediately.

## Recommended Fix
1. Update `pom.xml` configuration for `dependency-check-maven` to read `<nvdApiKey>${env.NVD_API_KEY}</nvdApiKey>`.
2. Add a fallback or allow developer builds to skip the remote check with `-Ddependency-check.skip=true` unless explicitly triggered in CI.
