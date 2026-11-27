# Issue #01: Critical Accessibility Barrier — Missing Form Labels and Accessible Names on New Expense Request Form

- **Title:** Missing `<label>` Associations and Accessible Names on Expense Item Description and Amount Inputs
- **Category:** Usability & Accessibility (WCAG 2.1 AA)
- **Severity:** Major
- **Priority:** High (P1)
- **Status:** Closed (Fixed in Commit `53f7568`)
- **Triage Decision:** Must-fix before release; completely blocks assistive technology users from submitting expense claims.
- **Linked Risk Register ID:** **PR-08** (*UI accessibility & keyboard navigation barriers*, Score: 9)
- **Evidence Link:** [`evidence/m3/axe/before/new_request_axe.json`](../../evidence/m3/axe/before/new_request_axe.json) and [`evidence/m3/lighthouse/before/new-request.report.html`](../../evidence/m3/lighthouse/before/new-request.report.html)

---

## Description & User Impact
On `/requests/new`, form controls for line items (`description`, `category`, and `amount`) were rendered with naked `<input>` elements lacking matching `<label for="...">` or `aria-label` attributes. Screen readers (NVDA, JAWS) announced only *"Edit text, blank"* without informing blind or low-vision users what data to input.

## Steps to Reproduce
1. Log in as an employee (`alice@acme.com`).
2. Navigate to `http://localhost:5173/requests/new`.
3. Run an automated accessibility scan using `@axe-core/playwright`.
4. Inspect violations: `label` rule violated on `.stack input[type="text"]` and `input[type="number"]`.

## Expected vs Actual
- **Expected:** Every interactive input has an associated programmatic label or descriptive accessible name per WCAG 1.3.1 (Info and Relationships) and 4.1.2 (Name, Role, Value).
- **Actual:** Inputs had no accessible name (`aria-label` or `<label>`), resulting in 5 serious Axe violations and a Lighthouse accessibility score of 75/100.

## Resolution
Added explicit HTML `id` attributes and `<label htmlFor="...">` bindings across all line item fields in `frontend/src/pages/NewRequest.tsx`. Verified post-fix Lighthouse score increased to **100/100** and Axe violations dropped to **0**.
