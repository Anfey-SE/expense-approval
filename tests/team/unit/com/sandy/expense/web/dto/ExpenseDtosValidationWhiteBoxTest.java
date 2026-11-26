package com.sandy.expense.web.dto;

import static org.assertj.core.api.Assertions.assertThat;

import com.sandy.expense.web.dto.ExpenseDtos.CreateRequest;
import com.sandy.expense.web.dto.ExpenseDtos.DecisionInput;
import com.sandy.expense.web.dto.ExpenseDtos.ItemInput;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/**
 * Boundary-value and equivalence-class tests for the Jakarta Bean Validation constraints declared in
 * {@link ExpenseDtos}. Pure unit tests: no Spring context, no database.
 *
 * <p>Member 2 tests the same limits through the HTTP API (integration level). These are unit-level
 * tests and are counted at the unit level only.
 *
 * <p>See {@code docs/team/07_boundary_tests.md} for the full equivalence-class listing and the
 * mapping of every test to its class and boundary.
 */
class ExpenseDtosValidationWhiteBoxTest {

    private static Validator validator;

    @BeforeAll
    static void setUpValidator() {
        try (ValidatorFactory factory = Validation.buildDefaultValidatorFactory()) {
            validator = factory.getValidator();
        }
    }

    // ================================================================
    // helpers
    // ================================================================

    private static ItemInput validItem() {
        return new ItemInput("Lunch", "Food", new BigDecimal("25.00"), LocalDate.now());
    }

    private static List<ItemInput> nItems(int n) {
        return Collections.nCopies(n, validItem());
    }

    private static <T> void assertValid(T object) {
        Set<ConstraintViolation<T>> violations = validator.validate(object);
        assertThat(violations).as("expected no violations but got: %s", violations).isEmpty();
    }

    private static <T> void assertInvalid(T object, String propertyPath) {
        Set<ConstraintViolation<T>> violations = validator.validate(object);
        assertThat(violations)
                .as("expected a violation on '%s'", propertyPath)
                .isNotEmpty()
                .anyMatch(v -> v.getPropertyPath().toString().equals(propertyPath));
    }

    // ================================================================
    // CreateRequest -- title: @NotBlank @Size(max = 200)
    // ================================================================

    @Test
    void title_blank_isInvalid() {
        assertInvalid(new CreateRequest("   ", null, null, List.of(validItem())), "title");
    }

    @Test
    void title_singleChar_isValid() {
        assertValid(new CreateRequest("A", null, null, List.of(validItem())));
    }

    @Test
    void title_at199chars_isValid() {
        assertValid(new CreateRequest("T".repeat(199), null, null, List.of(validItem())));
    }

    @Test
    void title_at200chars_isValid() {
        assertValid(new CreateRequest("T".repeat(200), null, null, List.of(validItem())));
    }

    @Test
    void title_at201chars_isInvalid() {
        assertInvalid(new CreateRequest("T".repeat(201), null, null, List.of(validItem())), "title");
    }

    // ================================================================
    // CreateRequest -- description: @Size(max = 2000), nullable
    // ================================================================

    @Test
    void description_null_isValid() {
        assertValid(new CreateRequest("T", null, null, List.of(validItem())));
    }

    @Test
    void description_at1999chars_isValid() {
        assertValid(new CreateRequest("T", "D".repeat(1999), null, List.of(validItem())));
    }

    @Test
    void description_at2000chars_isValid() {
        assertValid(new CreateRequest("T", "D".repeat(2000), null, List.of(validItem())));
    }

    @Test
    void description_at2001chars_isInvalid() {
        assertInvalid(
                new CreateRequest("T", "D".repeat(2001), null, List.of(validItem())), "description");
    }

    // ================================================================
    // CreateRequest -- currency: @Size(min = 3, max = 3), nullable
    // ================================================================

    @Test
    void currency_null_isValid() {
        assertValid(new CreateRequest("T", null, null, List.of(validItem())));
    }

    @Test
    void currency_2chars_isInvalid() {
        assertInvalid(new CreateRequest("T", null, "AB", List.of(validItem())), "currency");
    }

    @Test
    void currency_3chars_isValid() {
        assertValid(new CreateRequest("T", null, "USD", List.of(validItem())));
    }

    @Test
    void currency_4chars_isInvalid() {
        assertInvalid(new CreateRequest("T", null, "ABCD", List.of(validItem())), "currency");
    }

    // ================================================================
    // CreateRequest -- items: @NotEmpty @Size(max = 100) @Valid
    // ================================================================

    @Test
    void items_emptyList_isInvalid() {
        assertInvalid(new CreateRequest("T", null, null, List.of()), "items");
    }

    @Test
    void items_1item_isValid() {
        assertValid(new CreateRequest("T", null, null, nItems(1)));
    }

    @Test
    void items_at99items_isValid() {
        assertValid(new CreateRequest("T", null, null, nItems(99)));
    }

    @Test
    void items_at100items_isValid() {
        assertValid(new CreateRequest("T", null, null, nItems(100)));
    }

    @Test
    void items_at101items_isInvalid() {
        assertInvalid(new CreateRequest("T", null, null, nItems(101)), "items");
    }

    // ================================================================
    // ItemInput -- description: @NotBlank @Size(max = 200)
    // ================================================================

    @Test
    void itemDescription_blank_isInvalid() {
        assertInvalid(
                new ItemInput("   ", "Food", new BigDecimal("1.00"), LocalDate.now()), "description");
    }

    @Test
    void itemDescription_at199chars_isValid() {
        assertValid(new ItemInput("D".repeat(199), "Food", new BigDecimal("1.00"), LocalDate.now()));
    }

    @Test
    void itemDescription_at200chars_isValid() {
        assertValid(new ItemInput("D".repeat(200), "Food", new BigDecimal("1.00"), LocalDate.now()));
    }

    @Test
    void itemDescription_at201chars_isInvalid() {
        assertInvalid(
                new ItemInput("D".repeat(201), "Food", new BigDecimal("1.00"), LocalDate.now()),
                "description");
    }

    // ================================================================
    // ItemInput -- category: @NotBlank @Size(max = 40)
    // ================================================================

    @Test
    void itemCategory_blank_isInvalid() {
        assertInvalid(
                new ItemInput("Lunch", "   ", new BigDecimal("1.00"), LocalDate.now()), "category");
    }

    @Test
    void itemCategory_at39chars_isValid() {
        assertValid(
                new ItemInput("Lunch", "C".repeat(39), new BigDecimal("1.00"), LocalDate.now()));
    }

    @Test
    void itemCategory_at40chars_isValid() {
        assertValid(
                new ItemInput("Lunch", "C".repeat(40), new BigDecimal("1.00"), LocalDate.now()));
    }

    @Test
    void itemCategory_at41chars_isInvalid() {
        assertInvalid(
                new ItemInput("Lunch", "C".repeat(41), new BigDecimal("1.00"), LocalDate.now()),
                "category");
    }

    // ================================================================
    // ItemInput -- amount: @NotNull @Positive @Digits(integer = 10, fraction = 2)
    // ================================================================

    @Test
    void itemAmount_null_isInvalid() {
        assertInvalid(new ItemInput("Lunch", "Food", null, LocalDate.now()), "amount");
    }

    @Test
    void itemAmount_zero_isInvalid() {
        assertInvalid(
                new ItemInput("Lunch", "Food", BigDecimal.ZERO, LocalDate.now()), "amount");
    }

    @Test
    void itemAmount_oneCent_isValid() {
        assertValid(new ItemInput("Lunch", "Food", new BigDecimal("0.01"), LocalDate.now()));
    }

    @Test
    void itemAmount_10integerDigits_isValid() {
        assertValid(
                new ItemInput("Lunch", "Food", new BigDecimal("9999999999.99"), LocalDate.now()));
    }

    @Test
    void itemAmount_11integerDigits_isInvalid() {
        assertInvalid(
                new ItemInput("Lunch", "Food", new BigDecimal("10000000000.00"), LocalDate.now()),
                "amount");
    }

    @Test
    void itemAmount_2fractionDigits_isValid() {
        assertValid(new ItemInput("Lunch", "Food", new BigDecimal("1.99"), LocalDate.now()));
    }

    @Test
    void itemAmount_3fractionDigits_isInvalid() {
        assertInvalid(
                new ItemInput("Lunch", "Food", new BigDecimal("1.001"), LocalDate.now()), "amount");
    }

    // ================================================================
    // ItemInput -- incurredOn: @NotNull @PastOrPresent
    // ================================================================

    @Test
    void itemIncurredOn_null_isInvalid() {
        assertInvalid(new ItemInput("Lunch", "Food", new BigDecimal("1.00"), null), "incurredOn");
    }

    @Test
    void itemIncurredOn_yesterday_isValid() {
        assertValid(
                new ItemInput(
                        "Lunch", "Food", new BigDecimal("1.00"), LocalDate.now().minusDays(1)));
    }

    @Test
    void itemIncurredOn_today_isValid() {
        assertValid(new ItemInput("Lunch", "Food", new BigDecimal("1.00"), LocalDate.now()));
    }

    @Test
    void itemIncurredOn_tomorrow_isInvalid() {
        assertInvalid(
                new ItemInput(
                        "Lunch", "Food", new BigDecimal("1.00"), LocalDate.now().plusDays(1)),
                "incurredOn");
    }

    // ================================================================
    // DecisionInput -- comment: @Size(max = 500), nullable
    // ================================================================

    @Test
    void decisionComment_null_isValid() {
        assertValid(new DecisionInput(null));
    }

    @Test
    void decisionComment_at499chars_isValid() {
        assertValid(new DecisionInput("C".repeat(499)));
    }

    @Test
    void decisionComment_at500chars_isValid() {
        assertValid(new DecisionInput("C".repeat(500)));
    }

    @Test
    void decisionComment_at501chars_isInvalid() {
        assertInvalid(new DecisionInput("C".repeat(501)), "comment");
    }
}
