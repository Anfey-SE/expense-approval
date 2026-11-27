# Issue #02: Security Header Defect — Missing Anti-Clickjacking Header (`X-Frame-Options` / CSP `frame-ancestors`)

- **Title:** Missing Anti-Clickjacking Protection Exposes Application to UI Redressing Attacks
- **Category:** Defensive Security / Web Application Hardening
- **Severity:** Major
- **Priority:** High (P1)
- **Status:** Open (Documented with Remediation Plan)
- **Triage Decision:** Prioritized for next sprint; requires updating Spring Security configuration to include frame restrictions.
- **Linked Risk Register ID:** **PR-07** (*JWT / SecurityConfig exposure*, Score: 10)
- **Evidence Link:** [`evidence/m3/zap/summary.md`](../../evidence/m3/zap/summary.md) and [`evidence/m3/zap/zap-report.html`](../../evidence/m3/zap/zap-report.html)

---

## Description & Security Impact
During the OWASP ZAP passive proxy inspection across Workflow 1 and Workflow 2, ZAP flagged CWE-1021 (*Improper Restriction of Rendered UI Layers or Frames*). Neither the Spring Boot REST API (`:8081`) nor the frontend reverse proxy emitted `X-Frame-Options` or `Content-Security-Policy: frame-ancestors`. An attacker could embed the Expense Approval MIS inside a transparent `<iframe>` on a malicious website to trick authenticated managers or finance personnel into clicking disguised "Approve" buttons (Clickjacking).

## Steps to Reproduce
1. Start Spring Boot backend and Vite dev server.
2. Proxy browser traffic through OWASP ZAP (`http://localhost:8080`).
3. Complete request creation and manager approval.
4. Export ZAP alert list: Observe 6 alerts for `Missing Anti-clickjacking Header` on `/*` routes.

## Expected vs Actual
- **Expected:** HTTP responses must include `X-Frame-Options: DENY` (or `SAMEORIGIN`) and `Content-Security-Policy: frame-ancestors 'none'`.
- **Actual:** Neither header is set on HTTP responses from Spring Boot or Vite.

## Recommended Fix
In `com.sandy.expense.security.SecurityConfig.java`, update the `SecurityFilterChain` definition:
```java
http.headers(headers -> headers
    .frameOptions(frame -> frame.deny())
    .contentSecurityPolicy(csp -> csp.policyDirectives("frame-ancestors 'none'"))
);
```
