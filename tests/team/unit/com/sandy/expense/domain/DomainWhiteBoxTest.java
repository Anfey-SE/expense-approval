package com.sandy.expense.domain;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.EnumSource;

/**
 * Member 1 white-box tests for the BR3 state machine ({@link RequestStatus}) and the
 * {@link ExpenseRequest} total/aggregate logic. The full 5-state transition table is asserted, so
 * any new state or changed transition fails here first (live-task friendly).
 */
class DomainWhiteBoxTest {

    /** state, approverRole (or NONE), onApprove (or NONE) -- the complete BR3/BR4 table. */
    @ParameterizedTest
    @CsvSource({
        "DRAFT,            NONE,    NONE",
        "SUBMITTED,        MANAGER, MANAGER_APPROVED",
        "MANAGER_APPROVED, FINANCE, FINANCE_APPROVED",
        "FINANCE_APPROVED, NONE,    NONE",
        "REJECTED,         NONE,    NONE"
    })
    void transitionTable(RequestStatus from, String approver, String next) {
        Role expectedRole = approver.equals("NONE") ? null : Role.valueOf(approver);
        RequestStatus expectedNext = next.equals("NONE") ? null : RequestStatus.valueOf(next);
        assertThat(from.approverRole()).isEqualTo(expectedRole);
        assertThat(from.onApprove()).isEqualTo(expectedNext);
    }

    @ParameterizedTest
    @EnumSource(RequestStatus.class)
    void approverRoleIsNullExactlyWhenOnApproveIsNull(RequestStatus s) {
        assertThat(s.approverRole() == null).isEqualTo(s.onApprove() == null);
    }

    @Test
    void enumsExposeExpectedConstants() {
        assertThat(RequestStatus.values()).hasSize(5);
        assertThat(Role.values()).containsExactly(Role.EMPLOYEE, Role.MANAGER, Role.FINANCE);
        assertThat(ApprovalAction.values())
                .containsExactly(ApprovalAction.SUBMIT, ApprovalAction.APPROVE, ApprovalAction.REJECT);
    }

    @Test
    void recomputeTotal_noItems_isZeroWithScaleTwo() {
        ExpenseRequest r = new ExpenseRequest();
        r.recomputeTotal();
        assertThat(r.getTotalAmount().toPlainString()).isEqualTo("0.00");
    }

    @Test
    void recomputeTotal_sumsItems_atScaleTwo() {
        ExpenseRequest r = new ExpenseRequest();
        r.addItem(item("10.10"));
        r.addItem(item("0.20"));
        r.recomputeTotal();
        assertThat(r.getTotalAmount().toPlainString()).isEqualTo("10.30");
    }

    @Test
    void addItem_setsBackReference_andKeepsOrder() {
        ExpenseRequest r = new ExpenseRequest();
        ExpenseItem a = item("1.00");
        ExpenseItem b = item("2.00");
        r.addItem(a);
        r.addItem(b);
        assertThat(a.getRequest()).isSameAs(r);
        assertThat(r.getItems()).containsExactly(a, b);
    }

    @Test
    void newRequest_defaultsToDraftUsdZeroTotal() {
        ExpenseRequest r = new ExpenseRequest();
        assertThat(r.getStatus()).isEqualTo(RequestStatus.DRAFT);
        assertThat(r.getCurrency()).isEqualTo("USD");
        assertThat(r.getTotalAmount()).isEqualByComparingTo(BigDecimal.ZERO);
        assertThat(r.getApprovals()).isEmpty();
    }

    private static ExpenseItem item(String amount) {
        ExpenseItem i = new ExpenseItem();
        i.setDescription("d");
        i.setCategory("c");
        i.setAmount(new BigDecimal(amount));
        i.setIncurredOn(LocalDate.now());
        return i;
    }
}
