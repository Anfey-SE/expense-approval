# Issue #03: Security Header Defect — Content Security Policy (CSP) Header Not Set

- **Title:** Missing Content Security Policy Header Increases Blast Radius of Cross-Site Scripting (XSS)
- **Category:** Defensive Security / Web Application Hardening
- **Severity:** Medium
- **Priority:** Medium (P2)
- **Status:** Open (Documented with Remediation Plan)
- **Triage Decision:** Scheduled for hardening sprint; define baseline script and connect directives.
- **Linked Risk Register ID:** **PR-07** (*JWT / SecurityConfig exposure*, Score: 10)
- **Evidence Link:** [`evidence/m3/zap/summary.md`](../../evidence/m3/zap/summary.md) and [`evidence/m3/zap/zap-report.json`](../../evidence/m3/zap/zap-report.json)

---

## Description & Security Impact
OWASP ZAP identified that no `Content-Security-Policy` header was returned by the web server (CWE-693). Without CSP, modern browser defense-in-depth mechanisms are bypassed, allowing unrestricted inline script execution, style injection, or exfiltration of sensitive JWT tokens via untrusted external domain fetches if an XSS flaw ever emerges.

## Steps to Reproduce
1. Inspect HTTP response headers of `http://localhost:5173/` or `http://localhost:8081/api/requests`.
2. Check for `Content-Security-Policy` or `X-Content-Security-Policy`.
3. Note absence of header across all 58 sampled transactions.

## Expected vs Actual
- **Expected:** `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost:8081;`.
- **Actual:** Header is completely absent.

## Recommended Fix
Add a baseline CSP header in Spring Security configuration or within Vite's production index template/nginx server block.
