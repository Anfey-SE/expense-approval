# Accessibility & Usability Issues Log — Member 3 (24i-0761)

This log merges duplicate issues identified by Lighthouse and `@axe-core/playwright` across the key application screens (`/login`, `/`, `/requests/new`, `/requests/:id`). Issues found by both tools are consolidated into single entries.

All linked risks reference the project risk register maintained in [`docs/team/08_risk_register_and_exit_criteria.md`](../team/08_risk_register_and_exit_criteria.md).

---

## 1. Merged Accessibility Issues Table

| Issue ID | Screen | Element / Target | Found By | User Impact | Proposed Fix | Severity | Linked Risk ID |
|---|---|---|---|---|---|---|---|
| **A11Y-01** | All Screens (`/`, `/requests/new`, `/requests/:id`, `/login`) | `<div className="container">` in `Layout.tsx` & root div in `Login.tsx` | Both (Lighthouse: `landmark-one-main` + Axe: `landmark-one-main`, `region`) | Screen reader users cannot jump directly to primary content using landmark navigation keys. | Replace `<div className="container">` with semantic `<main className="container">` in `Layout.tsx` and `<main>` in `Login.tsx`. | Moderate | **PR-08** |
| **A11Y-02** | All Screens | `.subtitle`, `label`, `p.muted` (CSS variable `--muted: #6b7885`) | Both (Lighthouse: `color-contrast` + Axe: `color-contrast`) | Contrast ratio (~4.1:1) fails WCAG 2 AA minimum threshold (4.5:1), making labels hard to read for low-vision users. | Darken `--muted` in `index.css` to `#475569`, providing 6.2:1 contrast ratio against white/light backgrounds. | Serious | **PR-08** |
| **A11Y-03** | `/requests/new` | Title input, Description textarea, Currency input, and line item inputs | Both (Lighthouse: `label` + Axe: `label`) | Screen readers announce unlabelled textboxes; visually impaired employees cannot identify input fields. | Add explicit `id` attributes to inputs and matching `htmlFor` attributes to `<label>` tags. | Critical | **PR-08** |
| **A11Y-04** | `/requests/new` | Line item Category `<select>` | Both (Lighthouse: `select-name` + Axe: `select-name`) | Screen readers cannot announce the purpose of the category dropdown. | Add `id={`item-category-${idx}`}` and `<label htmlFor="...">Category</label>`, plus `aria-label="Category"`. | Critical | **PR-08** |
| **A11Y-05** | `/requests/new` | Line item remove button `<button title="Remove">✕</button>` | Axe (`button-name`) | Screen readers announce unicode multiplication sign "✕" rather than an actionable function. | Add `aria-label="Remove line item"` to the button. | Serious | **PR-08** |
| **A11Y-06** | `/` (Request List) | Status filter dropdown `<select>` | Both (Lighthouse: `label` + Axe: `select-name`) | Users cannot determine that the dropdown filters the table by request status. | Add `aria-label="Filter requests by status"` or associate with an explicit label. | Critical | **PR-08** |
| **A11Y-07** | `/login` | `input[type="email"]`, `input[type="password"]` | Both (Lighthouse: `label` + Axe: `label`) | Login credentials fields are not linked to their label text. | Add `id="login-email"` and `htmlFor="login-email"`, `id="login-password"` and `htmlFor="login-password"`. | Critical | **PR-08** |
| **A11Y-08** | `/requests/:id` | Actions decision input `<input maxlength="500">` | Both (Lighthouse: `label` + Axe: `label`) | Approvers using screen readers do not hear the "Comment (optional)" label when focused on the decision input. | Add `id="decision-comment"` and `htmlFor="decision-comment"`. | Critical | **PR-08** |
| **A11Y-09** | `/requests/:id` | `<h3>Approval trail</h3>` | Axe (`heading-order`) | Heading level skips from `h1` directly to `h3`, disrupting screen reader heading-level outline. | Change `<h3>` to `<h2>` to maintain semantic hierarchical sequence. | Moderate | **PR-08** |

---

## 2. Summary by Severity

- **Critical:** 4 issues (`A11Y-03`, `A11Y-04`, `A11Y-06`, `A11Y-07`, `A11Y-08`)
- **Serious:** 2 issues (`A11Y-02`, `A11Y-05`)
- **Moderate:** 2 issues (`A11Y-01`, `A11Y-09`)
- **Total Unique Accessibility Defects:** 9 issues

---

## 3. Before vs After Accessibility Remediation Verification

Remediation was performed on the primary data entry screen: **`/requests/new`** (`frontend/src/pages/NewRequest.tsx`).
Fixes applied:
1. Associated all form inputs, textareas, and selects with explicit `<label>` elements via `id` and `htmlFor`.
2. Added `aria-label="Category"` to the line item category selector.
3. Added `aria-label="Remove line item"` to the item removal button.
4. Wrapped page content in semantic `<main role="main">` landmark.
5. Boosted subtitle and label contrast to `#334155` (>7:1 contrast ratio against `#ffffff`).

### Before / After Score Comparison Table

| Screen | Phase | Lighthouse A11y | Lighthouse Best Practices | Lighthouse SEO | Axe Total Violations | Axe Critical + Serious | Status / Change |
|---|---|---|---|---|---|---|---|
| **`/requests/new` (Fixed)** | **Before** | **75** | **100** | **82** | **5** | **3** (2 crit, 1 serious) | Baseline |
| **`/requests/new` (Fixed)** | **After** | **100** | **100** | **82** | **0** | **0** (0 crit, 0 serious) | **+25 pts LH, -5 Axe (100% resolved)** |
| `/login` | Before | 75 | 100 | 82 | 4 | 2 (1 crit, 1 serious) | Unmodified baseline |
| `/login` | After | 75 | 100 | 82 | 4 | 2 (1 crit, 1 serious) | Control screen |
| `/` (Requests List) | Before | 75 | 100 | 82 | 4 | 2 (1 crit, 1 serious) | Unmodified baseline |
| `/` (Requests List) | After | 79 | 100 | 82 | 4 | 2 (1 crit, 1 serious) | Control screen |
| `/requests/:id` | Before | 75 | 100 | 82 | 5 | 2 (1 crit, 1 serious) | Unmodified baseline |
| `/requests/:id` | After | 76 | 100 | 82 | 5 | 2 (1 crit, 1 serious) | Control screen |

All evidence files are archived in:
- Axe: [`evidence/m3/axe/before/`](../../evidence/m3/axe/before/) and [`evidence/m3/axe/after/`](../../evidence/m3/axe/after/)
- Lighthouse: [`evidence/m3/lighthouse/before/`](../../evidence/m3/lighthouse/before/) and [`evidence/m3/lighthouse/after/`](../../evidence/m3/lighthouse/after/)

