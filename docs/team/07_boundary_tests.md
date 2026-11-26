# Task C — Boundary Value Analysis & Equivalence Classes

## 1. Source constraints

All constraints are declared in [`ExpenseDtos.java`](../../src/main/java/com/sandy/expense/web/dto/ExpenseDtos.java) (lines 28–46) using Jakarta Bean Validation annotations.

```java
// ExpenseDtos.java lines 28-46
public record ItemInput(
        @NotBlank @Size(max = 200) String description,                              // line 29
        @NotBlank @Size(max = 40) String category,                                  // line 30
        @NotNull @Positive
                @Digits(integer = 10, fraction = 2, ...) BigDecimal amount,         // lines 31-34
        @NotNull @PastOrPresent(...) LocalDate incurredOn) {}                        // line 35

public record CreateRequest(
        @NotBlank @Size(max = 200) String title,                                    // line 38
        @Size(max = 2000) String description,                                       // line 39
        @Size(min = 3, max = 3) String currency,                                   // line 40
        @NotEmpty(...) @Size(max = 100, ...) @Valid List<ItemInput> items) {}        // lines 41-44

public record DecisionInput(@Size(max = 500) String comment) {}                     // line 46
```

---

## 2. Equivalence classes

### CreateRequest fields

| Field | EC | Class | Valid? | Representative |
|-------|-----|-------|--------|----------------|
| **title** | E1 | non-blank, 1-200 chars | Valid | `"Business Trip"` |
| | E2 | null | Invalid | `null` |
| | E3 | blank / whitespace only | Invalid | `"   "` |
| | E4 | > 200 chars | Invalid | `"T".repeat(201)` |
| **description** | E5 | null | Valid | `null` |
| | E6 | 0-2000 chars | Valid | `"some text"` |
| | E7 | > 2000 chars | Invalid | `"D".repeat(2001)` |
| **currency** | E8 | null | Valid | `null` |
| | E9 | exactly 3 chars | Valid | `"USD"` |
| | E10 | < 3 chars | Invalid | `"AB"` |
| | E11 | > 3 chars | Invalid | `"ABCD"` |
| **items** | E12 | 1-100 valid items | Valid | `List.of(validItem())` |
| | E13 | empty list | Invalid | `List.of()` |
| | E14 | > 100 items | Invalid | `nItems(101)` |

### ItemInput fields

| Field | EC | Class | Valid? | Representative |
|-------|-----|-------|--------|----------------|
| **description** | E15 | non-blank, 1-200 chars | Valid | `"Lunch"` |
| | E16 | blank | Invalid | `"   "` |
| | E17 | > 200 chars | Invalid | `"D".repeat(201)` |
| **category** | E18 | non-blank, 1-40 chars | Valid | `"Food"` |
| | E19 | blank | Invalid | `"   "` |
| | E20 | > 40 chars | Invalid | `"C".repeat(41)` |
| **amount** | E21 | positive, <=10 int digits, <=2 frac digits | Valid | `25.00` |
| | E22 | null | Invalid | `null` |
| | E23 | zero | Invalid | `0` |
| | E24 | > 10 integer digits | Invalid | `10000000000.00` |
| | E25 | > 2 fraction digits | Invalid | `1.001` |
| **incurredOn** | E26 | past or today | Valid | `LocalDate.now()` |
| | E27 | null | Invalid | `null` |
| | E28 | future | Invalid | `tomorrow` |

### DecisionInput fields

| Field | EC | Class | Valid? | Representative |
|-------|-----|-------|--------|----------------|
| **comment** | E29 | null or 0-500 chars | Valid | `null`, `"Approved"` |
| | E30 | > 500 chars | Invalid | `"C".repeat(501)` |

---

## 3. Boundary test matrix

Each test validates exactly **one invalid value** (all other fields are valid).
Test class: [`ExpenseDtosValidationWhiteBoxTest.java`](../../tests/team/unit/com/sandy/expense/web/dto/ExpenseDtosValidationWhiteBoxTest.java)

### CreateRequest -- title

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `title_blank_isInvalid` | @NotBlank | `"   "` | E3 | violation on `title` |
| `title_singleChar_isValid` | @NotBlank min | `"A"` (1 char) | E1 | valid |
| `title_at199chars_isValid` | @Size below max | 199 chars | E1 | valid |
| `title_at200chars_isValid` | @Size at max | 200 chars | E1 | valid |
| `title_at201chars_isInvalid` | @Size above max | 201 chars | E4 | violation on `title` |

### CreateRequest -- description

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `description_null_isValid` | nullable | `null` | E5 | valid |
| `description_at1999chars_isValid` | @Size below max | 1999 chars | E6 | valid |
| `description_at2000chars_isValid` | @Size at max | 2000 chars | E6 | valid |
| `description_at2001chars_isInvalid` | @Size above max | 2001 chars | E7 | violation on `description` |

### CreateRequest -- currency

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `currency_null_isValid` | nullable | `null` | E8 | valid |
| `currency_2chars_isInvalid` | @Size below min | `"AB"` | E10 | violation on `currency` |
| `currency_3chars_isValid` | @Size at exact | `"USD"` | E9 | valid |
| `currency_4chars_isInvalid` | @Size above max | `"ABCD"` | E11 | violation on `currency` |

### CreateRequest -- items count

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `items_emptyList_isInvalid` | @NotEmpty | 0 items | E13 | violation on `items` |
| `items_1item_isValid` | @NotEmpty at min | 1 item | E12 | valid |
| `items_at99items_isValid` | @Size below max | 99 items | E12 | valid |
| `items_at100items_isValid` | @Size at max | 100 items | E12 | valid |
| `items_at101items_isInvalid` | @Size above max | 101 items | E14 | violation on `items` |

### ItemInput -- description

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `itemDescription_blank_isInvalid` | @NotBlank | `"   "` | E16 | violation on `description` |
| `itemDescription_at199chars_isValid` | @Size below max | 199 chars | E15 | valid |
| `itemDescription_at200chars_isValid` | @Size at max | 200 chars | E15 | valid |
| `itemDescription_at201chars_isInvalid` | @Size above max | 201 chars | E17 | violation on `description` |

### ItemInput -- category

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `itemCategory_blank_isInvalid` | @NotBlank | `"   "` | E19 | violation on `category` |
| `itemCategory_at39chars_isValid` | @Size below max | 39 chars | E18 | valid |
| `itemCategory_at40chars_isValid` | @Size at max | 40 chars | E18 | valid |
| `itemCategory_at41chars_isInvalid` | @Size above max | 41 chars | E20 | violation on `category` |

### ItemInput -- amount

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `itemAmount_null_isInvalid` | @NotNull | `null` | E22 | violation on `amount` |
| `itemAmount_zero_isInvalid` | @Positive | `0` | E23 | violation on `amount` |
| `itemAmount_oneCent_isValid` | @Positive min | `0.01` | E21 | valid |
| `itemAmount_10integerDigits_isValid` | @Digits at max int | `9999999999.99` | E21 | valid |
| `itemAmount_11integerDigits_isInvalid` | @Digits above max int | `10000000000.00` | E24 | violation on `amount` |
| `itemAmount_2fractionDigits_isValid` | @Digits at max frac | `1.99` | E21 | valid |
| `itemAmount_3fractionDigits_isInvalid` | @Digits above max frac | `1.001` | E25 | violation on `amount` |

### ItemInput -- incurredOn

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `itemIncurredOn_null_isInvalid` | @NotNull | `null` | E27 | violation on `incurredOn` |
| `itemIncurredOn_yesterday_isValid` | @PastOrPresent past | yesterday | E26 | valid |
| `itemIncurredOn_today_isValid` | @PastOrPresent present | today | E26 | valid |
| `itemIncurredOn_tomorrow_isInvalid` | @PastOrPresent future | tomorrow | E28 | violation on `incurredOn` |

### DecisionInput -- comment

| Test method | Boundary | Value | EC | Expected |
|-------------|----------|-------|----|----------|
| `decisionComment_null_isValid` | nullable | `null` | E29 | valid |
| `decisionComment_at499chars_isValid` | @Size below max | 499 chars | E29 | valid |
| `decisionComment_at500chars_isValid` | @Size at max | 500 chars | E29 | valid |
| `decisionComment_at501chars_isInvalid` | @Size above max | 501 chars | E30 | violation on `comment` |

---

## 4. Test level and overlap note

> [!IMPORTANT]
> These tests exercise the Jakarta Bean Validation `Validator` directly on the DTO records, with **no Spring context and no database**. They are pure **unit-level** boundary tests.
>
> **Member 2** tests the same input limits through the HTTP API (integration level), verifying that Spring MVC returns 400 for each constraint violation. The two levels are complementary: unit tests confirm the annotation wiring, integration tests confirm the web layer enforces it.
>
> These tests are counted at the **unit level only**.

---

## 5. Total boundary tests

| Record | Tests |
|--------|-------|
| `CreateRequest` (title, description, currency, items) | 18 |
| `ItemInput` (description, category, amount, incurredOn) | 19 |
| `DecisionInput` (comment) | 4 |
| **Total** | **41** |
