package com.sandy.expense.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.sandy.expense.domain.ApprovalAction;
import com.sandy.expense.domain.Department;
import com.sandy.expense.domain.ExpenseItem;
import com.sandy.expense.domain.ExpenseRequest;
import com.sandy.expense.domain.RequestStatus;
import com.sandy.expense.domain.Role;
import com.sandy.expense.domain.User;
import com.sandy.expense.repo.ExpenseRequestRepository;
import com.sandy.expense.repo.UserRepository;
import com.sandy.expense.security.AppUserPrincipal;
import com.sandy.expense.web.dto.ExpenseDtos.CreateRequest;
import com.sandy.expense.web.dto.ExpenseDtos.ItemInput;
import com.sandy.expense.web.dto.ExpenseDtos.RequestDetail;
import com.sandy.expense.web.error.ApiException;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

/**
 * Member 1 white-box tests for {@link ExpenseService}. Goal: 100% statement + branch coverage of
 * the service, with a documented MC/DC set for the critical decision {@code assertCanDecide}
 * (see docs/team/03_mcdc_and_cfg.md). Each test name states the branch it drives.
 *
 * <p>Business rules referenced: BR1 submit needs items, BR2 manager approval decision
 * (role + department + not-self), BR3 state transitions, BR4 finance stage ownership.
 */
@ExtendWith(MockitoExtension.class)
class ExpenseServiceWhiteBoxTest {

    @Mock ExpenseRequestRepository requests;
    @Mock UserRepository users;
    @InjectMocks ExpenseService service;

    private final Department eng = dept(1L, "Engineering");
    private final Department sales = dept(2L, "Sales");
    private final Department finDept = dept(3L, "Finance");

    private User alice;
    private User bob;
    private User dave;
    private User carol;
    private User fiona;
    private User noDept;

    private static final Pageable PAGE = PageRequest.of(0, 20);

    /** Users are built here (not in field initialisers) because the mocks exist only after injection. */
    @BeforeEach
    void setUpUsers() {
        alice = user(10L, "Alice", Role.EMPLOYEE, eng);
        bob = user(11L, "Bob", Role.MANAGER, eng);
        dave = user(12L, "Dave", Role.MANAGER, sales);
        carol = user(13L, "Carol", Role.EMPLOYEE, sales);
        fiona = user(14L, "Fiona", Role.FINANCE, finDept);
        noDept = user(15L, "Nodept", Role.EMPLOYEE, null);
    }

    // =====================================================================
    // create()  -- branches: user missing, no department, currency x3, description x2
    // =====================================================================

    @Test
    void create_nullCurrencyAndDescription_defaultsToUsdAndEmpty() {
        stubUser(alice);
        RequestDetail d = service.create(principal(alice), new CreateRequest("Trip", null, null, items("25.50")));

        assertThat(d.currency()).isEqualTo("USD");
        assertThat(d.description()).isEmpty();
        assertThat(d.status()).isEqualTo("DRAFT");
        assertThat(d.totalAmount()).isEqualByComparingTo("25.50");
        assertThat(d.approvals()).isEmpty();
        verify(requests).save(org.mockito.ArgumentMatchers.any(ExpenseRequest.class));
    }

    @Test
    void create_blankCurrency_defaultsToUsd() {
        stubUser(alice);
        RequestDetail d = service.create(principal(alice), new CreateRequest("Trip", "x", "   ", items("1.00")));
        assertThat(d.currency()).isEqualTo("USD");
    }

    @Test
    void create_lowercaseCurrency_isUppercased_andDescriptionKept() {
        stubUser(alice);
        RequestDetail d = service.create(principal(alice), new CreateRequest("Trip", "dinner", "eur", items("1.00")));
        assertThat(d.currency()).isEqualTo("EUR");
        assertThat(d.description()).isEqualTo("dinner");
    }

    @Test
    void create_amountIsRoundedHalfUpToTwoDecimals_andTotalIsSum() {
        stubUser(alice);
        RequestDetail d =
                service.create(principal(alice), new CreateRequest("Trip", null, null, items("12.345", "0.005")));
        // 12.345 -> 12.35, 0.005 -> 0.01 (HALF_UP); total 12.36
        assertThat(d.items()).extracting(i -> i.amount().toPlainString()).containsExactly("12.35", "0.01");
        assertThat(d.totalAmount().toPlainString()).isEqualTo("12.36");
    }

    @Test
    void create_copiesTitleAndAllItemFields() {
        stubUser(alice);
        LocalDate date = LocalDate.of(2026, 3, 15);
        ItemInput inputItem = new ItemInput("Airfare", "Travel", new BigDecimal("350.00"), date);
        RequestDetail d =
                service.create(
                        principal(alice),
                        new CreateRequest("Client Summit", "Hotel & flights", "usd", List.of(inputItem)));

        assertThat(d.title()).isEqualTo("Client Summit");
        assertThat(d.items()).hasSize(1);
        assertThat(d.items().get(0).description()).isEqualTo("Airfare");
        assertThat(d.items().get(0).category()).isEqualTo("Travel");
        assertThat(d.items().get(0).incurredOn()).isEqualTo(date);
    }

    @Test
    void create_userNotFound_throwsNotFound() {
        when(users.findById(10L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.create(principal(alice), new CreateRequest("T", null, null, items("1"))))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("User not found");
    }

    @Test
    void create_userWithoutDepartment_throwsNoDepartment() {
        stubUser(noDept);
        assertThatThrownBy(() -> service.create(principal(noDept), new CreateRequest("T", null, null, items("1"))))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NO_DEPARTMENT");
    }

    // =====================================================================
    // list() -- the three role arms of the switch + requireDept() null/non-null
    // =====================================================================

    @Test
    void list_employee_usesRequesterScope() {
        ExpenseRequest r = request(1L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.forRequester(alice.getId(), null, PAGE)).thenReturn(page(r));

        assertThat(service.list(principal(alice), null, PAGE).content()).hasSize(1);
        verify(requests).forRequester(alice.getId(), null, PAGE);
    }

    @Test
    void list_manager_usesDepartmentScope_withStatusFilter() {
        ExpenseRequest r = request(2L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.forDepartment(eng.getId(), RequestStatus.SUBMITTED, PAGE)).thenReturn(page(r));

        assertThat(service.list(principal(bob), RequestStatus.SUBMITTED, PAGE).content()).hasSize(1);
        verify(requests).forDepartment(eng.getId(), RequestStatus.SUBMITTED, PAGE);
    }

    @Test
    void list_finance_seesEverything() {
        ExpenseRequest r = request(3L, carol, sales, RequestStatus.MANAGER_APPROVED);
        when(requests.forAll(null, PAGE)).thenReturn(page(r));

        assertThat(service.list(principal(fiona), null, PAGE).content()).hasSize(1);
        verify(requests).forAll(null, PAGE);
    }

    @Test
    void list_managerWithoutDepartment_throwsNoDepartment() {
        AppUserPrincipal deptless = new AppUserPrincipal(99L, "m@acme.com", null, Role.MANAGER, null);
        assertThatThrownBy(() -> service.list(deptless, null, PAGE))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NO_DEPARTMENT");
    }

    // =====================================================================
    // get() / assertCanView() -- not found + each role x (visible | hidden)
    // =====================================================================

    @Test
    void get_missingRequest_throwsNotFound() {
        when(requests.findWithDetailById(404L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.get(principal(alice), 404L))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("not found");
    }

    @Test
    void get_employeeOwner_canView() {
        ExpenseRequest r = request(5L, alice, eng, RequestStatus.DRAFT);
        when(requests.findWithDetailById(5L)).thenReturn(Optional.of(r));
        assertThat(service.get(principal(alice), 5L).id()).isEqualTo(5L);
    }

    @Test
    void get_employeeNotOwner_getsNotFoundNotForbidden() {
        ExpenseRequest r = request(6L, alice, eng, RequestStatus.DRAFT);
        when(requests.findWithDetailById(6L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.get(principal(carol), 6L))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getStatus().value())
                .isEqualTo(404);
    }

    @Test
    void get_managerSameDepartment_canView() {
        ExpenseRequest r = request(7L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findWithDetailById(7L)).thenReturn(Optional.of(r));
        assertThat(service.get(principal(bob), 7L).id()).isEqualTo(7L);
    }

    @Test
    void get_managerOtherDepartment_getsNotFound() {
        ExpenseRequest r = request(8L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findWithDetailById(8L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.get(principal(dave), 8L))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getStatus().value())
                .isEqualTo(404);
    }

    @Test
    void get_finance_canViewAnyDepartment() {
        ExpenseRequest r = request(9L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findWithDetailById(9L)).thenReturn(Optional.of(r));
        assertThat(service.get(principal(fiona), 9L).id()).isEqualTo(9L);
    }

    // =====================================================================
    // update() -- not found, not owner, not DRAFT, currency x3, description x2
    // =====================================================================

    @Test
    void update_missingRequest_throwsNotFound() {
        when(requests.findById(404L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.update(principal(alice), 404L, new CreateRequest("T", null, null, items("1"))))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("not found");
    }

    @Test
    void update_notOwner_isForbidden() {
        ExpenseRequest r = request(20L, alice, eng, RequestStatus.DRAFT);
        when(requests.findById(20L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.update(principal(bob), 20L, new CreateRequest("T", null, null, items("1"))))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("only edit your own");
    }

    @Test
    void update_requestNotDraft_isConflict_andRequestUnchanged() {
        ExpenseRequest r = request(21L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(21L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.update(principal(alice), 21L, new CreateRequest("T", null, null, items("1"))))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NOT_EDITABLE");
        assertThat(r.getTitle()).isEqualTo("Test request");
    }

    @Test
    void update_nullCurrency_keepsExistingCurrency_andClearsDescription() {
        ExpenseRequest r = request(22L, alice, eng, RequestStatus.DRAFT);
        r.setCurrency("GBP");
        r.addItem(item("Old", "Misc", "5.00"));
        when(requests.findById(22L)).thenReturn(Optional.of(r));

        RequestDetail d = service.update(principal(alice), 22L, new CreateRequest("New", null, null, items("7.00", "3.00")));

        assertThat(d.currency()).isEqualTo("GBP");
        assertThat(d.description()).isEmpty();
        assertThat(d.title()).isEqualTo("New");
        assertThat(d.items()).hasSize(2); // old item replaced
        assertThat(d.totalAmount()).isEqualByComparingTo("10.00");
    }

    @Test
    void update_blankCurrency_keepsExistingCurrency() {
        ExpenseRequest r = request(23L, alice, eng, RequestStatus.DRAFT);
        r.setCurrency("GBP");
        when(requests.findById(23L)).thenReturn(Optional.of(r));
        RequestDetail d = service.update(principal(alice), 23L, new CreateRequest("New", "d", " ", items("1.00")));
        assertThat(d.currency()).isEqualTo("GBP");
        assertThat(d.description()).isEqualTo("d");
    }

    @Test
    void update_newCurrency_isUppercased() {
        ExpenseRequest r = request(24L, alice, eng, RequestStatus.DRAFT);
        when(requests.findById(24L)).thenReturn(Optional.of(r));
        RequestDetail d = service.update(principal(alice), 24L, new CreateRequest("New", null, "eur", items("1.00")));
        assertThat(d.currency()).isEqualTo("EUR");
    }

    // =====================================================================
    // submit()  (BR1 + BR3) -- not found, owner, DRAFT, items, success
    // =====================================================================

    @Test
    void submit_missingRequest_throwsNotFound() {
        when(requests.findById(404L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.submit(principal(alice), 404L)).isInstanceOf(ApiException.class);
    }

    @Test
    void submit_success_movesToSubmitted_writesOneSubmitTrailRow() {
        ExpenseRequest r = request(30L, alice, eng, RequestStatus.DRAFT);
        r.addItem(item("Flight", "Travel", "420.00"));
        when(requests.findById(30L)).thenReturn(Optional.of(r));

        RequestDetail d = service.submit(principal(alice), 30L);

        assertThat(d.status()).isEqualTo("SUBMITTED");
        assertThat(d.submittedAt()).isNotNull();
        assertThat(r.getApprovals()).hasSize(1);
        assertThat(r.getApprovals().get(0).getAction()).isEqualTo(ApprovalAction.SUBMIT);
        assertThat(r.getApprovals().get(0).getFromStatus()).isEqualTo(RequestStatus.DRAFT);
        assertThat(r.getApprovals().get(0).getToStatus()).isEqualTo(RequestStatus.SUBMITTED);
        assertThat(r.getApprovals().get(0).getComment()).isEmpty();
    }

    @Test
    void submit_notOwner_isForbidden() {
        ExpenseRequest r = request(31L, alice, eng, RequestStatus.DRAFT);
        r.addItem(item("x", "y", "1.00"));
        when(requests.findById(31L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.submit(principal(bob), 31L))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("only submit your own");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.DRAFT);
        assertThat(r.getApprovals()).isEmpty();
    }

    @ParameterizedTest
    @EnumSource(
            value = RequestStatus.class,
            names = {"SUBMITTED", "MANAGER_APPROVED", "FINANCE_APPROVED", "REJECTED"})
    void submit_anyNonDraftStatus_isConflict(RequestStatus status) {
        ExpenseRequest r = request(32L, alice, eng, status);
        r.addItem(item("x", "y", "1.00"));
        when(requests.findById(32L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.submit(principal(alice), 32L))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NOT_SUBMITTABLE");
        assertThat(r.getStatus()).isEqualTo(status);
        assertThat(r.getApprovals()).isEmpty();
    }

    @Test
    void submit_draftWithNoItems_isRejected_BR1() {
        // Unreachable through the HTTP API (@NotEmpty on CreateRequest.items) but reachable at the
        // service boundary: defensive branch, documented in the equivalent-branch notes.
        ExpenseRequest r = request(33L, alice, eng, RequestStatus.DRAFT);
        when(requests.findById(33L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.submit(principal(alice), 33L))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("EMPTY_REQUEST");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.DRAFT);
        assertThat(r.getApprovals()).isEmpty();
    }

    // =====================================================================
    // approve()/reject() -- assertCanDecide() MC/DC (BR2, BR3, BR4)
    //
    //   D1: needed == null                       (state awaits nobody)
    //   D2: me.role != needed                    (role owns the stage)
    //   D3: A && B  where A = needed == MANAGER, B = request dept != my dept
    //   D4: requester == me                      (no self-decision)
    // =====================================================================

    @ParameterizedTest
    @EnumSource(
            value = RequestStatus.class,
            names = {"DRAFT", "FINANCE_APPROVED", "REJECTED"})
    void approve_statusAwaitingNobody_isNotPending_D1(RequestStatus status) {
        ExpenseRequest r = request(40L, alice, eng, status);
        when(requests.findById(40L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(bob), 40L, ""))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NOT_PENDING");
        assertThat(r.getStatus()).isEqualTo(status);
        assertThat(r.getApprovals()).isEmpty();
    }

    @ParameterizedTest
    @EnumSource(
            value = RequestStatus.class,
            names = {"DRAFT", "FINANCE_APPROVED", "REJECTED"})
    void reject_statusAwaitingNobody_isNotPending_D1(RequestStatus status) {
        ExpenseRequest r = request(41L, alice, eng, status);
        when(requests.findById(41L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.reject(principal(bob), 41L, "no"))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NOT_PENDING");
        assertThat(r.getApprovals()).isEmpty();
    }

    @Test
    void approve_missingRequest_throwsNotFound() {
        when(requests.findById(404L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.approve(principal(bob), 404L, "")).isInstanceOf(ApiException.class);
    }

    @Test
    void approve_employeeOnSubmitted_wrongRole_D2() {
        ExpenseRequest r = request(42L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(42L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(carol), 42L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("MANAGER");
    }

    @Test
    void approve_managerOnManagerApproved_wrongRole_D2() {
        ExpenseRequest r = request(43L, alice, eng, RequestStatus.MANAGER_APPROVED);
        when(requests.findById(43L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(bob), 43L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("FINANCE");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.MANAGER_APPROVED);
    }

    /** MC/DC for D3, condition A: pair (this) vs managerOtherDepartment_D3_BtoTrue. */
    @Test
    void approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false() {
        // A = false (needed is FINANCE). Department mismatch (Finance != Engineering) must NOT matter.
        ExpenseRequest r = request(44L, alice, eng, RequestStatus.MANAGER_APPROVED);
        when(requests.findById(44L)).thenReturn(Optional.of(r));
        RequestDetail d = service.approve(principal(fiona), 44L, "paid");
        assertThat(d.status()).isEqualTo("FINANCE_APPROVED");
    }

    /** MC/DC for D3: A = true, B = true -> denied. */
    @Test
    void approve_managerOtherDepartment_isForbidden_D3_BtoTrue() {
        ExpenseRequest r = request(45L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(45L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(dave), 45L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("own department");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.SUBMITTED);
        assertThat(r.getApprovals()).isEmpty();
    }

    /** MC/DC for D3: A = true, B = false -> allowed (pair partner for condition B). */
    @Test
    void approve_managerSameDepartment_isAllowed_D3_BtoFalse() {
        ExpenseRequest r = request(46L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(46L)).thenReturn(Optional.of(r));
        RequestDetail d = service.approve(principal(bob), 46L, "ok");
        assertThat(d.status()).isEqualTo("MANAGER_APPROVED");
        assertThat(r.getApprovals()).hasSize(1);
        var a = r.getApprovals().get(0);
        assertThat(a.getAction()).isEqualTo(ApprovalAction.APPROVE);
        assertThat(a.getFromStatus()).isEqualTo(RequestStatus.SUBMITTED);
        assertThat(a.getToStatus()).isEqualTo(RequestStatus.MANAGER_APPROVED);
        assertThat(a.getActor()).isSameAs(bob);
    }

    @Test
    void approve_setsApprovalRequestBackReference() {
        ExpenseRequest r = request(56L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(56L)).thenReturn(Optional.of(r));
        service.approve(principal(bob), 56L, "ok");
        assertThat(r.getApprovals().get(0).getRequest()).isSameAs(r);
    }

    /** D3 with a manager whose principal carries no department: B evaluates true -> denied. */
    @Test
    void approve_managerPrincipalWithoutDepartment_isForbidden() {
        ExpenseRequest r = request(47L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(47L)).thenReturn(Optional.of(r));
        AppUserPrincipal deptless = new AppUserPrincipal(77L, "m@acme.com", null, Role.MANAGER, null);
        assertThatThrownBy(() -> service.approve(deptless, 47L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("own department");
    }

    /** D4 true for a manager (existing upstream test also covers; kept for MC/DC completeness). */
    @Test
    void approve_managerOnOwnRequest_isForbidden_D4_true() {
        ExpenseRequest r = request(48L, bob, eng, RequestStatus.SUBMITTED);
        when(requests.findById(48L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(bob), 48L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("your own request");
        assertThat(r.getApprovals()).isEmpty();
    }

    /** D4 true for FINANCE as requester (distinct path: D3 short-circuits to false first). */
    @Test
    void approve_financeOnOwnRequest_isForbidden_D4_true() {
        ExpenseRequest r = request(49L, fiona, finDept, RequestStatus.MANAGER_APPROVED);
        when(requests.findById(49L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.approve(principal(fiona), 49L, ""))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("your own request");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.MANAGER_APPROVED);
    }

    @Test
    void approve_nullComment_isStoredAsEmptyString() {
        ExpenseRequest r = request(50L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(50L)).thenReturn(Optional.of(r));
        service.approve(principal(bob), 50L, null);
        assertThat(r.getApprovals().get(0).getComment()).isEmpty();
    }

    // ---- reject(): BR3 transitions into REJECTED from both review stages ----

    @Test
    void reject_managerOnSubmitted_setsRejected_withReason() {
        ExpenseRequest r = request(51L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(51L)).thenReturn(Optional.of(r));
        RequestDetail d = service.reject(principal(bob), 51L, "missing receipt");
        assertThat(d.status()).isEqualTo("REJECTED");
        var a = r.getApprovals().get(0);
        assertThat(a.getAction()).isEqualTo(ApprovalAction.REJECT);
        assertThat(a.getFromStatus()).isEqualTo(RequestStatus.SUBMITTED);
        assertThat(a.getToStatus()).isEqualTo(RequestStatus.REJECTED);
        assertThat(a.getComment()).isEqualTo("missing receipt");
    }

    @Test
    void reject_financeOnManagerApproved_setsRejected() {
        ExpenseRequest r = request(52L, alice, eng, RequestStatus.MANAGER_APPROVED);
        when(requests.findById(52L)).thenReturn(Optional.of(r));
        RequestDetail d = service.reject(principal(fiona), 52L, null);
        assertThat(d.status()).isEqualTo("REJECTED");
        assertThat(r.getApprovals()).hasSize(1);
        assertThat(r.getApprovals().get(0).getFromStatus()).isEqualTo(RequestStatus.MANAGER_APPROVED);
    }

    @Test
    void reject_managerOtherDepartment_isForbidden() {
        ExpenseRequest r = request(53L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(53L)).thenReturn(Optional.of(r));
        assertThatThrownBy(() -> service.reject(principal(dave), 53L, "no"))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("own department");
        assertThat(r.getStatus()).isEqualTo(RequestStatus.SUBMITTED);
    }

    @Test
    void reject_twice_secondAttemptIsNotPending_andTrailHasExactlyOneRow() {
        ExpenseRequest r = request(54L, alice, eng, RequestStatus.SUBMITTED);
        when(requests.findById(54L)).thenReturn(Optional.of(r));
        service.reject(principal(bob), 54L, "no");
        assertThatThrownBy(() -> service.reject(principal(bob), 54L, "no again"))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("NOT_PENDING");
        assertThat(r.getApprovals()).hasSize(1);
    }

    @Test
    void fullHappyPath_draftToFinanceApproved_hasThreeTrailRowsInOrder() {
        ExpenseRequest r = request(55L, alice, eng, RequestStatus.DRAFT);
        r.addItem(item("Hotel", "Travel", "200.00"));
        when(requests.findById(55L)).thenReturn(Optional.of(r));

        service.submit(principal(alice), 55L);
        service.approve(principal(bob), 55L, "ok");
        service.approve(principal(fiona), 55L, "paid");

        assertThat(r.getStatus()).isEqualTo(RequestStatus.FINANCE_APPROVED);
        assertThat(r.getApprovals())
                .extracting(a -> a.getAction() + ":" + a.getFromStatus() + ">" + a.getToStatus())
                .containsExactly(
                        "SUBMIT:DRAFT>SUBMITTED",
                        "APPROVE:SUBMITTED>MANAGER_APPROVED",
                        "APPROVE:MANAGER_APPROVED>FINANCE_APPROVED");
    }

    // =====================================================================
    // fixtures
    // =====================================================================

    private void stubUser(User u) {
        lenient().when(users.findById(u.getId())).thenReturn(Optional.of(u));
    }

    private static Department dept(long id, String name) {
        Department d = new Department(name);
        d.setId(id);
        return d;
    }

    private User user(long id, String name, Role role, Department dept) {
        User u = new User();
        u.setId(id);
        u.setFullName(name);
        u.setEmail(name.toLowerCase() + "@acme.com");
        u.setPasswordHash("x");
        u.setRole(role);
        u.setDepartment(dept);
        // transition() resolves the actor through getReferenceById
        lenient().when(users.getReferenceById(id)).thenReturn(u);
        return u;
    }

    private static AppUserPrincipal principal(User u) {
        return AppUserPrincipal.fromUser(u);
    }

    private static ExpenseRequest request(long id, User requester, Department dept, RequestStatus status) {
        ExpenseRequest r = new ExpenseRequest();
        r.setId(id);
        r.setRequester(requester);
        r.setDepartment(dept);
        r.setStatus(status);
        r.setTitle("Test request");
        r.setCurrency("USD");
        return r;
    }

    private static ExpenseItem item(String desc, String category, String amount) {
        ExpenseItem i = new ExpenseItem();
        i.setDescription(desc);
        i.setCategory(category);
        i.setAmount(new BigDecimal(amount));
        i.setIncurredOn(LocalDate.now());
        return i;
    }

    private static List<ItemInput> items(String... amounts) {
        return java.util.Arrays.stream(amounts)
                .map(a -> new ItemInput("Item", "Misc", new BigDecimal(a), LocalDate.now()))
                .toList();
    }

    private static Page<ExpenseRequest> page(ExpenseRequest... rs) {
        return new PageImpl<>(List.of(rs), PAGE, rs.length);
    }
}
