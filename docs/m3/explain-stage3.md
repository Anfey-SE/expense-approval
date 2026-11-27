# Stage 3 Explanation: Defensive Security

**Author:** Member 3 (roll no. 24i-0761, Section C)  
**Date:** November 2026  
**Audience:** Beginner / Peer Reviewers / Viva Examination Panel  

---

## 1. What Was Done and Why

In Stage 3, we evaluated the defensive security posture of the Expense Approval MIS across four critical dimensions:
1. **Route and Authorization Mapping:** Mapped every REST endpoint and UI page to the business roles and data permissions.
2. **Access Control Decision Verification:** Implemented automated Playwright tests exercising five distinct access decisions across all 5 operational roles (Employee Owner, Other Employee, Manager Same Dept, Manager Other Dept, Finance). Both direct REST API responses and rendered React UI elements were validated.
3. **Passive Security Scanning with OWASP ZAP:** Deployed an OWASP ZAP container in passive proxy mode (`http://localhost:8080`) and drove complete user journeys through Workflow 1 (Draft to Submission) and Workflow 2 (Manager to Finance Approval) to capture HTTP requests and response headers without performing active attacks or disruptive scanning.
4. **Security Control Reviews:** Deep-dived into Spring Security implementation code for (a) Stateless JWT Token/Session Management, and (b) Multi-Layer Authorization (PreAuthorize + Service-layer checks).
5. **Software Supply Chain Dependency Audits:** Ran `npm audit` on the React frontend and `dependency-check:check` on the Spring Boot Maven backend.

---

## 2. What Each Test Asserts

Our automated security suite is located in [`tests/team/security/access_control.spec.ts`](../../tests/team/security/access_control.spec.ts):

1. **Decision 1 (Allowed: Manager Same Department):**
   - *API:* `POST /api/requests/{id}/approve` with Bob's token returns HTTP `200 OK` with JSON field `status: "MANAGER_APPROVED"`.
   - *UI:* Bob logs into the React app, visits `/requests/{id}`, and confirms the status badge reads `manager approved` and his approval comment is displayed in the audit trail.
2. **Decision 2 (Denied: Manager Other Department):**
   - *API:* Dave (`Sales Manager`) attempts to approve Alice's Engineering request. The API returns HTTP `403 FORBIDDEN` with code `"FORBIDDEN"` and message `"You can only decide on requests in your own department"`.
   - *UI:* Dave views the request; the UI suppresses approval action buttons.
3. **Decision 3 (Denied: Other Employee Horizontal Privilege Escalation):**
   - *API:* Carol (`Sales Employee`) attempts to view Alice's request. The backend returns HTTP `404 NOT FOUND` (defensive concealment). A subsequent direct modification attempt returns HTTP `403 FORBIDDEN`.
   - *UI:* Carol navigates to `/requests/{id}` and sees `"Request not found"` instead of confidential expense data.
4. **Decision 4 (Allowed: Finance Final Approval):**
   - *API:* Fiona (`Finance`) approves a `MANAGER_APPROVED` request. The API returns HTTP `200 OK` with `status: "FINANCE_APPROVED"`.
   - *UI:* Fiona visits the request and verifies the green badge `finance approved`.
5. **Decision 5 (Denied: Employee Owner Self-Approval):**
   - *API:* Alice attempts to approve her own submitted request. The API returns HTTP `403 FORBIDDEN` (`"You cannot decide on your own request"`).
   - *UI:* Requester view renders only line item details and approval trail; no decision action buttons exist.

---

## 3. What Each Tool Output Means

### 3.1 OWASP ZAP Passive Scan (`evidence/m3/zap/summary.md`)
- **Passive Proxy Mode:** ZAP acted strictly as an intermediary forwarding traffic between Playwright and Vite/Spring Boot without injecting SQL payloads, fuzzing parameters, or attempting brute force.
- **Missing Anti-clickjacking Header (Medium, CWE-1021):** The backend does not send `X-Frame-Options: DENY` or `Content-Security-Policy: frame-ancestors 'none'`. This allows malicious sites to embed the application inside an invisible `<iframe>` and trick users into clicking buttons (UI redressing / clickjacking).
- **Missing Content Security Policy (Medium, CWE-693):** Without a CSP header, the browser has no restrictions on where scripts, images, or stylesheets can be loaded from, increasing the blast radius of potential Cross-Site Scripting (XSS).
- **Missing X-Content-Type-Options (Low, CWE-693):** Missing `X-Content-Type-Options: nosniff` header allows older browsers to treat non-executable MIME types as executable JavaScript if they detect script-like syntax.

### 3.2 Dependency Audits (`evidence/m3/security/`)
- **Frontend (`npm audit`):** Scanned 168 packages and flagged 2 High-severity CVEs:
  - `vite` SSRF/arbitrary file read in development mode (GHSA-c647-8m2c-5878).
  - `source-map-js` ReDoS parsing weakness.
- **Backend (`dependency-check-maven`):** Highlighted the modern operational requirement of the NVD 2.0 API requiring an authorized API key (`nvdApiKey`) to avoid rate limit throttling and download failures.

---

## 4. 5 Likely Viva Questions and Concise Answers

### Q1: What is the difference between passive and active security scanning in OWASP ZAP?
**Answer:** Passive scanning observes and analyzes normal traffic (requests and responses) flowing through the proxy without modifying payloads or injecting hostile inputs. Active scanning deliberately sends malicious payloads (e.g., SQL injection strings, XSS scripts, path traversal tokens) against endpoints to trigger vulnerabilities. For this assignment, we strictly used passive scanning to safely analyze headers and data flows without destabilizing the system.

### Q2: Why does the backend return 404 Not Found instead of 403 Forbidden when another employee views a request?
**Answer:** Returning `403 Forbidden` confirms to an attacker that the request ID exists, enabling horizontal resource enumeration (IDOR). Returning `404 Not Found` conceals whether the resource exists at all, providing defense-in-depth against ID guessing attacks.

### Q3: How does the application enforce multi-layer authorization?
**Answer:** It uses defense-in-depth:
1. **Web Layer:** Spring Security uses `@PreAuthorize("hasAnyRole('MANAGER','FINANCE')")` on controller methods to verify the user's role before executing the method.
2. **Service Layer:** `ExpenseService.assertCanDecide` verifies department ownership (`me.getDepartmentId().equals(r.getDepartment().getId())`), lifecycle state (`SUBMITTED` vs `MANAGER_APPROVED`), and blocks self-approval (`!r.getRequester().getId().equals(me.getUserId())`).

### Q4: Why is CSRF disabled in `SecurityConfig.java`? Is this a vulnerability?
**Answer:** No, CSRF is safely disabled because the backend uses stateless JWT authentication passed via the `Authorization: Bearer <token>` HTTP header rather than automatic session cookies. Browsers do not automatically attach custom `Authorization` headers on cross-site form submissions, mitigating the CSRF threat vector.

### Q5: What is the severity and remediation for the missing anti-clickjacking header flagged by ZAP?
**Answer:** It is a Medium-severity issue (CWE-1021). It can be remediated in Spring Security by configuring `.headers(h -> h.frameOptions(fo -> fo.deny()))` and setting `Content-Security-Policy: frame-ancestors 'none'`. This prevents the application from being framed on third-party domains.
