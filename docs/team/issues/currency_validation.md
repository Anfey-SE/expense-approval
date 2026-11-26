# GitHub Issue — Non-alphabetic `currency` codes (e.g. `"123"`) accepted by `ExpenseDtos.CreateRequest`

## Title
`ExpenseDtos.CreateRequest` accepts non-alphabetic 3-character currency codes such as `"123"`

## Severity
**Medium** (Input validation / data integrity defect — allows invalid non-ISO-4217 currency strings to be persisted)

## Affected Code
- `src/main/java/com/sandy/expense/web/dto/ExpenseDtos.java` line 40:
  ```java
  @Size(min = 3, max = 3) String currency,
  ```

## Steps to Reproduce
1. Construct a `CreateRequest` with `currency = "123"` and valid `title` and `items`:
   ```java
   new CreateRequest("T", null, "123", List.of(validItem()))
   ```
2. Validate it with Jakarta Bean Validation `Validator.validate(request)` (or submit `POST /api/expenses` with `"currency": "123"`).

## Expected Behavior
Validation rejects `"123"` with a constraint violation on `currency` because ISO 4217 currency codes consist of 3 alphabetic letters (`[A-Za-z]{3}`), not digits or symbols.

## Actual Behavior
`@Size(min = 3, max = 3)` only checks string length, so `"123"` passes Jakarta Bean Validation with **0 violations** and `ExpenseService.create` stores `"123"` as the request's currency.

## Empirical Confirmation
Unit test `ExpenseDtosValidationWhiteBoxTest.currency_numeric123_isInvalid` calls `validator.validate(new CreateRequest("T", null, "123", List.of(validItem())))` and asserts a violation on `currency`. Against the unpatched `ExpenseDtos`, the test **fails** because `validator.validate(...)` returns an empty set (`Expecting actual not to be empty`).
