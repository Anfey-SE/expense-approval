# Observation: No edit UI for draft requests

**Type:** Observation (not a defect)
**Found by:** Member 1, during UC2 inspection
**Date:** 2026-11-26

## Summary

The backend exposes a `PUT /api/requests/{id}` endpoint
([ExpenseController.java L64-70](../../../src/main/java/com/sandy/expense/web/ExpenseController.java))
that allows updating a DRAFT request's title, description, currency, and line items.
However, the frontend never calls this endpoint — there is no edit form in the UI.

The `RequestDetail` page ([RequestDetail.tsx](../../../frontend/src/pages/RequestDetail.tsx))
only displays the request and offers action buttons ("Submit for approval" / "Approve" / "Reject").
Once a draft is created via the `NewRequest` form, the user cannot modify it through the UI.

## Impact

An employee who makes a mistake (e.g. wrong amount, wrong category) in the create form
must create a new request instead of editing the existing draft.

## Coverage

Member 2 covers the `PUT /api/requests/{id}` endpoint through API-level tests.
This observation is recorded so the team is aware the endpoint exists but has no UI.
