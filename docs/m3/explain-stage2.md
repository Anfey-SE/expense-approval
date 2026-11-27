# Stage 2: Usability and Accessibility Testing — Beginner's Guide & Viva Preparation

**Student Name:** Member 3 (Roll No. 24i-0761)  
**Course:** Software Quality Engineering (SE3002) — Section C  
**Target Module:** Expense Approval System — Stage 2 Deliverables  

---

## 1. What Was Done in Stage 2 and Why

### Summary of Activities
In this stage, we evaluated the usability and digital accessibility of the Expense Approval Management Information System (MIS) through automated user journeys, keyboard-only interaction testing, and industry-standard accessibility auditing tools:
1. **Automated Usability Task Tests:** Built Playwright end-to-end task tests simulating real employee workflows, specifically verifying that business rule validation errors are clearly communicated to the user, can be corrected, and yield positive confirmations.
2. **Pure Keyboard Navigation Testing:** Created a strict keyboard-only test using exclusively `Tab` and `Enter` keystrokes (zero mouse clicks or programmatic focusing) to ensure motor-impaired or keyboard-dependent users can navigate and submit expense requests.
3. **Comprehensive Accessibility Audits (Before Remediation):** Scanned all 4 primary application screens (`/login`, `/`, `/requests/new`, `/requests/:id`) using both Google Lighthouse (measuring Accessibility, Best Practices, and SEO) and `@axe-core/playwright` (scanning against WCAG 2.1 AA rules).
4. **Consolidated Issues Register:** De-duplicated findings from both tools into a unified issue register ([`docs/m3/a11y-issues.md`](./a11y-issues.md)) mapped to project risk IDs.
5. **Targeted Frontend Remediation:** Fixed accessibility defects on the primary data entry screen (`frontend/src/pages/NewRequest.tsx`).
6. **Post-Remediation Verification (After Scans):** Re-ran both Lighthouse and Axe-core audits, demonstrating that accessibility violations on the repaired screen dropped to zero and its Lighthouse accessibility score reached 100/100.

### Why Accessibility (A11y) and Usability Matter in SQE
- **Digital Inclusivity & Compliance:** Legal and ethical frameworks (such as WCAG 2.1 AA and Section 508) mandate that enterprise software must be operable by individuals with visual, motor, auditory, or cognitive disabilities.
- **Error Recovery:** Good usability ensures that users are not stranded when they make mistakes. The system must clearly explain what went wrong and allow seamless correction without data loss.
- **Automated Regression Prevention:** Manual accessibility checks can miss subtle contrast or DOM tree issues. Integrating automated linters and scanners (Axe and Lighthouse) prevents accessibility regressions during CI/CD.

---

## 2. What Each Test Asserts

All usability and keyboard navigation tests are located in [`tests/team/a11y/usability.spec.ts`](../../tests/team/a11y/usability.spec.ts).

### Test 1: Task 1 — Business Rule Error Recovery & Correction (`USABILITY-TASK-01`)
- **Action:** The employee attempts to create an expense request with an invalid 4-letter currency code (`USDD`).
- **Assertions:**
  1. Asserts that the form submission is rejected by the business rule.
  2. Asserts that a visible error message (`Currency must be a 3-letter ISO code`) appears on screen explaining the exact correction needed.
  3. Corrects the field value to `USD` and clicks "Save Draft".
  4. Asserts that the application successfully navigates to the newly created request page (`/requests/:id`) with status `DRAFT`, confirming successful error recovery.

### Test 2: Task 2 — Review & Approval Usability Journey (`USABILITY-TASK-02`)
- **Action:** Finance user Fiona logs in to review a pending expense request submitted by Alice.
- **Assertions:**
  1. Asserts that the inbox card displays the pending request.
  2. Enters an optional approval comment (`Audited and approved`).
  3. Clicks "Approve" and asserts immediate UI feedback (`Approved`).
  4. Asserts that the request status changes to `FINANCE_APPROVED` and the approval trail row appears in the audit table.

### Test 3: Keyboard Navigation — Tab/Enter Focus Sequence (`USABILITY-KEYBOARD-01`)
- **Action:** The user creates a complete expense request using only keyboard inputs (`Tab` to move focus, `Enter` to activate buttons, keyboard typing for form values).
- **Assertions:**
  1. Asserts that pressing `Tab` advances DOM focus in logical sequence: Title -> Description -> Currency -> Line Item Description -> Amount -> Category -> Save Draft button.
  2. Asserts that pressing `Enter` on the focused "Save Draft" button submits the form.
  3. Asserts navigation to `/requests/:id` and verifies the title on the saved request.

---

## 3. What the Tool Outputs Mean

### Google Lighthouse
Lighthouse is an open-source automated audit tool developed by Google:
- **Accessibility Score (0–100):** Weighted percentage of automated accessibility audits passed (e.g., color contrast, image alt attributes, form labels, ARIA landmarks).
- **Best Practices Score (0–100):** Checks modern web development standards (HTTPS, console error absence, secure resource handling).
- **SEO Score (0–100):** Evaluates mobile friendliness, metadata, and crawlability.

### Axe-core (`@axe-core/playwright`)
Axe-core is the industry-standard accessibility testing engine by Deque Systems. Unlike scoring tools, Axe reports discrete WCAG violation objects categorized by impact:
- **Critical:** Prevents disabled users from accessing core content or functionality (e.g., completely unlabelled form controls, missing select names).
- **Serious:** Causes major frustration or significant barriers (e.g., text failing color contrast ratios).
- **Moderate:** Minor barriers (e.g., missing `<main>` landmarks or non-sequential heading levels).
- **Minor:** Low-impact styling or semantic inconsistencies.

---

## 4. Before vs. After Remediation Results

| Metric | Before Fix (`/requests/new`) | After Fix (`/requests/new`) | Improvement |
|---|---|---|---|
| **Lighthouse Accessibility Score** | **75 / 100** | **100 / 100** | **+25 points (Perfect Score)** |
| **Lighthouse Best Practices** | 100 / 100 | 100 / 100 | Maintained (100%) |
| **Lighthouse SEO** | 82 / 100 | 82 / 100 | Maintained (82%) |
| **Axe Total Violations** | **5 violations** | **0 violations** | **100% defects eliminated** |
| **Axe Critical + Serious Violations** | **3 violations** | **0 violations** | **100% high-severity eliminated** |

### Fixes Applied to `NewRequest.tsx`:
1. Added explicit `id` attributes to inputs and connected them to `<label htmlFor="...">`.
2. Added `aria-label="Category"` to the line item category dropdown.
3. Added `aria-label="Remove line item"` to the item removal button.
4. Wrapped page contents in semantic `<main role="main">` landmark.
5. Replaced low-contrast text color `#6b7885` with `#334155` (>7:1 contrast).

---

## 5. Five Likely Viva Questions & Model Answers

### Q1: What is the difference between Axe-core and Google Lighthouse for accessibility testing?
**Answer:**
Google Lighthouse runs a subset of Axe-core rules combined with page performance and SEO audits, generating an overall weighted score from 0 to 100. Axe-core provides an in-depth, deterministic scan that categorizes specific WCAG rule violations by severity (critical, serious, moderate, minor), exact DOM selector, and suggested remediation code without subjective weighting.

### Q2: Why is associating an explicit `<label htmlFor="id">` superior to wrapping an `<input>` inside a `<label>`?
**Answer:**
While both are valid in HTML, explicit association using `htmlFor` and a matching input `id` has the broadest compatibility across older screen readers, assistive technology frameworks, and speech-recognition tools. It also ensures that clicking the label reliably focuses the input across all browsers without ambiguity.

### Q3: What is the WCAG 2.1 AA contrast ratio requirement for normal body text, and why did our baseline app fail it?
**Answer:**
WCAG 2.1 AA requires a minimum contrast ratio of **4.5:1** for normal text against its background (and 3:1 for large text). The baseline app used CSS variable `--muted: #6b7885` against a white background (`#ffffff`), producing a contrast ratio of only **4.1:1**, which fails the requirement. We resolved this by darkening the muted text to `#334155`, achieving a contrast ratio of over **7.2:1**.

### Q4: Why is automated keyboard navigation testing essential even if all UI buttons work with mouse clicks?
**Answer:**
Many users with motor disabilities, tremors, or repetitive strain injuries (as well as power users and screen reader users) navigate web applications exclusively using the keyboard (`Tab`, `Shift+Tab`, `Enter`, `Space`). Mouse-only event handlers (`onClick` on `<div>` tags without keyboard listeners) or broken DOM tab order (`tabindex` bugs) can make an application completely unusable for keyboard users.

### Q5: Can automated accessibility tools like Axe-core catch 100% of accessibility defects?
**Answer:**
No. Automated tools typically detect approximately 30% to 57% of all WCAG issues. They can detect missing labels, poor contrast, and missing landmarks, but they cannot evaluate subjective aspects such as whether screen reader announcement text makes semantic sense in context, whether error recovery instructions are intuitive, or whether screen magnification preserves layout coherence. Manual accessibility evaluation remains necessary.
