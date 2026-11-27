# Issue #04: Dependency Security Finding — High-Severity Vite Dev Server SSRF and Arbitrary File Read

- **Title:** Vite <= 6.1.6 Bundler Development Server SSRF and Path Traversal Vulnerability
- **Category:** Software Supply Chain / Dependency Security
- **Severity:** High (in dev environment) / Low (in production container)
- **Priority:** High (P1)
- **Status:** Open (Documented with Remediation Plan)
- **Triage Decision:** Triage as dev-dependency upgrade; execute `npm update vite` in frontend directory.
- **Linked Risk Register ID:** **PR-07** (*JWT / SecurityConfig exposure*, Score: 10)
- **Evidence Link:** [`evidence/m3/security/npm-audit.json`](../../evidence/m3/security/npm-audit.json) and [`evidence/m3/security/npm-audit.txt`](../../evidence/m3/security/npm-audit.txt)

---

## Description & Security Impact
`npm audit` identified GHSA-c647-8m2c-5878 and GHSA-9cwx-2883-4wmm affecting `vite` versions $\le 6.1.6$. In development mode, crafted WebSocket ping payloads or encoded URL requests can trigger Server-Side Request Forgery (SSRF) or arbitrary local file disclosure from the developer machine outside the project root. While production deployment serves static pre-compiled React bundles via Spring Boot, the vulnerability presents a genuine threat to local developer workstations and shared CI test runners.

## Steps to Reproduce
1. In `frontend/`, run `npm audit --json`.
2. Locate the advisory for `vite` package.
3. Observe high severity finding: CVSS 7.5.

## Expected vs Actual
- **Expected:** Frontend dependencies contain zero high-severity advisories.
- **Actual:** `vite` (version 6.1.0 installed) flagged with 2 high-severity CVEs.

## Recommended Fix
Run `cd frontend && npm install vite@^6.2.0 --save-dev` to patch the bundler engine.
