# Bug: UI displays generic "Request validation failed" instead of field-level validation error

**Severity:** Minor (UX)
**Component:** Frontend (`NewRequest.tsx` / `api.ts`)
**Found by:** Member 1, during UC2 (`UC2_E2_invalid_currency`)

## Steps to Reproduce

1. Log in as `alice@acme.com` (`password123`).
2. Click **New request** (`/requests/new`).
3. Fill in a valid Title and 1 valid line item.
4. Enter `123` in the **Currency** field.
5. Click **Create draft**.

## Expected Result

The UI should display the specific field validation message returned by the backend
(`"currency must be 3 letters"`), or at least include the failing field name (`currency`)
so the user knows which field to fix.

## Actual Result

The backend returns HTTP 400 with:
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "fields": { "currency": "currency must be 3 letters" }
}
```
`api.ts` parses `data.fields` onto `ApiError.fields` ([api.ts L82-84](../../../frontend/src/api.ts)),
but `NewRequest.tsx` only renders `err.message` ([NewRequest.tsx L44](../../../frontend/src/pages/NewRequest.tsx)),
so the `.error` div displays only the generic text:

> `Request validation failed`
