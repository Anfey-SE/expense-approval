# Root Cause Analysis (RCA) — Major Observed Defects

**Author:** Member 3 (roll no. 24i-0761, Section C)  
**Date:** November 2026  
**Techniques Applied:** 5 Whys Analysis, Ishikawa (Fishbone) Diagram, Pareto Distribution  

---

## 1. Defect Defect 1: Missing Anti-Clickjacking & Security Headers (CWE-1021 / CWE-693)

- **Linked Issue:** [Issue #02](issue-02.md) and [Issue #03](issue-03.md)
- **Observed By:** OWASP ZAP Passive Scan (`evidence/m3/zap/summary.md`)
- **Severity:** Major (CVSS 6.5)

### 1.1 The 5 Whys Analysis
1. **Why was the application vulnerable to Clickjacking / UI Redressing?**  
   Because HTTP responses from the backend and frontend did not contain `X-Frame-Options` or `Content-Security-Policy: frame-ancestors` headers.
2. **Why were the security headers missing from HTTP responses?**  
   Because Spring Security's `SecurityFilterChain` in `SecurityConfig.java` left default header configurations unspecified while explicitly configuring CSRF and session management.
3. **Why did the security configuration omit frame and CSP options?**  
   Because the initial system architecture assumed that since the backend is a stateless REST API emitting JSON, browser frame-rendering risks were solely a frontend concern.
4. **Why didn't the frontend development or build server supply these headers?**  
   Because the Vite development server proxy (`vite.config.ts`) simply forwards raw HTTP streams from port 8081 without injecting edge security headers.
5. **Why was this omission not detected prior to Stage 3?**  
   Because automated unit tests and integration tests focused strictly on HTTP status codes and payload assertions rather than defensive HTTP response headers.

### 1.2 Fishbone (Ishikawa) Diagram
The diagram is rendered and saved to [`evidence/m3/defects/fishbone_security.png`](../../evidence/m3/defects/fishbone_security.png):

![Fishbone Diagram: Missing Security Headers](../../evidence/m3/defects/fishbone_security.png)

### 1.3 Corrective & Preventive Action Plan (CAPA)
- **Immediate Correction:** Update `SecurityConfig.java` with explicit header DSL:
  ```java
  http.headers(h -> h
      .frameOptions(fo -> fo.deny())
      .contentSecurityPolicy(csp -> csp.policyDirectives("frame-ancestors 'none'; default-src 'self';"))
  );
  ```
- **Preventive Control:** Incorporate automated OWASP ZAP passive proxy scanning into the GitHub Actions CI pipeline (`.github/workflows/ci.yml`) to fail builds if required security headers are absent.

---

## 2. Defect 2: Accessibility Barrier on New Expense Request Form (WCAG 2.1 AA)

- **Linked Issue:** [Issue #01](issue-01.md)
- **Observed By:** Axe-core (`new_request_axe.json`) and Google Lighthouse
- **Severity:** Major (Assistive Technology Blocker)
- **Status:** Resolved in Commit `53f7568`

### 2.1 The 5 Whys Analysis
1. **Why could blind and motor-impaired users not complete an expense submission?**  
   Because screen readers announced line item inputs as *"edit text, blank"* without naming the field, and keyboard tab focus jumped unexpectedly.
2. **Why were the form fields unlabelled by assistive technology?**  
   Because the React JSX markup rendered raw `<input>` elements without matching `<label htmlFor="...">` attributes or `aria-label` tags.
3. **Why were labels omitted during UI development?**  
   Because the original UI prototype relied purely on visual placeholder text (`placeholder="Description"`, `placeholder="0.00"`), which is not an accessible name substitute.
4. **Why was placeholder-only design accepted?**  
   Because development was performed solely with visual browser inspection; no automated accessibility linters (`eslint-plugin-jsx-a11y`) were configured.
5. **Why was the defect undetected until Stage 2?**  
   Because existing Playwright E2E tests (UC1/UC2) used CSS class and type locators (`input[type="text"]`) rather than user-facing accessibility roles (`getByRole("textbox", { name: "Description" })`).

### 2.2 Corrective & Preventive Action Plan (CAPA)
- **Immediate Correction (Executed in `53f7568`):** Bound programmatic labels with explicit IDs (`#request-title`, `#item-desc-0`, `#item-amount-0`), introduced semantic `<main>` landmark, and updated Playwright locators to use accessible roles. Verified Lighthouse Accessibility increased from 75 to 100.
- **Preventive Control:** Install `eslint-plugin-jsx-a11y` in `frontend/package.json` to flag unlabelled inputs at compile time and mandate `@axe-core/playwright` checks on all new UI screens.

---

## 3. Pareto Analysis of Observed Findings

Across our real runs in Stages 1–4, a total of 48 distinct findings and weaknesses were cataloged across 5 categories:

| Defect / Weakness Category | Finding Count | Cumulative % | Priority Action |
|---|---|---|---|
| **Security Headers & Hardening (ZAP)** | 38 alerts | 79.2% | Configure Spring Security headers |
| **UI Accessibility & Form Usability** | 5 violations | 89.6% | Resolved via semantic labels (`53f7568`) |
| **Dependency Advisories (npm/NVD)** | 3 advisories | 95.8% | Upgrade `vite` and provide NVD API key |
| **Business Rule Guidance (EW-2)** | 1 weakness | 97.9% | Add `@NotBlank` on rejection comment |
| **CI Build & Pipeline Configuration** | 1 weakness | 100.0% | Update `pom.xml` dependency-check config |

The Pareto chart is preserved in [`evidence/m3/defects/pareto.png`](../../evidence/m3/defects/pareto.png):

![Pareto Chart](../../evidence/m3/defects/pareto.png)

**Key Insight:** Addressing the first two categories (Security Headers and UI Accessibility) resolves **89.6%** of all detected weaknesses in the application.
