# Task 6 — Mutation Testing Report (PIT)

## 1. Setup & Scope

Mutation testing runs with `org.pitest:pitest-maven:1.30.2` and `org.pitest:pitest-junit5-plugin:1.2.3`, configured in [`pom.xml`](../../pom.xml#L282-L319):

- **Target classes**: `com.sandy.expense.service.*`, `com.sandy.expense.domain.*`
- **Target tests (team unit suite only)**: `com.sandy.expense.*WhiteBoxTest` (`ExpenseServiceWhiteBoxTest`, `AuthServiceWhiteBoxTest`, `DomainWhiteBoxTest`)
- **Upstream integration tests (`src/test`)**: excluded from PIT so the mutation score reflects strictly Member 1's unit tests.
- **No exclusions**: no classes, methods, or lines are excluded from mutation, and no existing test was weakened or removed.

### Running PIT from a Fresh Machine

Because the custom mutator module (`com.sandy:pit-custom-mutators:1.0.0`) is a standalone Maven project under `tools/pit-custom-mutators/`, it must be installed into the local Maven repository before running PIT:

```bash
./mvnw -f tools/pit-custom-mutators/pom.xml clean install
./mvnw test-compile org.pitest:pitest-maven:mutationCoverage
```

*(On Windows PowerShell, use `.\mvnw` instead of `./mvnw`.)*

---

## 2. How a PIT Plugin Mutator Works (Plain English)

1. **Discovery (`ServiceLoader`) & JAR Manifest**: Before running tests, PIT scans its plugin classpath for JARs containing `META-INF/services/org.pitest.mutationtest.engine.gregor.MethodMutatorFactory`. That file lists the fully qualified class names of every custom mutator factory. When we first ran PIT against the custom mutator JAR without explicit manifest entries, PIT rejected the plugin at startup with:
   > `PitError: No implementation vendor in manifest of plugin jar for class com.sandy.pit.DropDepartmentCheckMutator`
   Adding `maven-jar-plugin` with `<manifestEntries>` (`Implementation-Title`, `Implementation-Version`, and `Implementation-Vendor`) in [`tools/pit-custom-mutators/pom.xml`](../../tools/pit-custom-mutators/pom.xml#L30-L47) resolved this.
2. **Bytecode rewriting (ASM)**: Java source is already compiled to JVM bytecode (`.class` files). PIT uses the ASM library to walk every instruction in each target method through a `MethodVisitor`.
3. **Mutant generation & toggle (`shouldMutate`)**: Whenever a mutator recognizes a target bytecode pattern (e.g., an `if` jump or static field load), it calls `context.registerMutation(...)` to assign a unique `MutationIdentifier`. During an actual test run for that mutant ID, `context.shouldMutate(id)` returns `true` only for that one mutant, so PIT emits mutated bytecode in memory without modifying source files on disk.
4. **Killing the mutant**: PIT runs the covering JUnit 5 tests against the mutated class in memory. If at least one test fails (or throws an unexpected error), the mutant is **KILLED**; if all tests still pass, it **SURVIVED**.

---

## 3. Custom Business-Rule Mutators (`tools/pit-custom-mutators/`)

We built a standalone Maven plugin module at [`tools/pit-custom-mutators/pom.xml`](../../tools/pit-custom-mutators/pom.xml) (`com.sandy:pit-custom-mutators:1.0.0`), installed into the local Maven repository before running PIT (building this module explicitly before PIT in CI is planned for Task 7).

SPI registration in [`META-INF/services/org.pitest.mutationtest.engine.gregor.MethodMutatorFactory`](../../tools/pit-custom-mutators/src/main/resources/META-INF/services/org.pitest.mutationtest.engine.gregor.MethodMutatorFactory#L1-L2):
```text
com.sandy.pit.DropDepartmentCheckMutator
com.sandy.pit.SwapApproverRoleMutator
```

### Custom Mutator 1 — `DROP_DEPARTMENT_CHECK` (BR2)
Source: [`DropDepartmentCheckMutator.java`](../../tools/pit-custom-mutators/src/main/java/com/sandy/pit/DropDepartmentCheckMutator.java#L16-L77).

- **Target production rule** (`ExpenseService.java:174`):
  ```java
  if (needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())) {
      throw ApiException.forbidden("You can only decide on requests in your own department");
  }
  ```
- **What the mutator does**: Inside `assertCanDecide`, it matches `AppUserPrincipal.getDepartmentId()` followed by `Long.equals(...)` and its `IFNE` branch instruction, pops the boolean comparison result off the operand stack, and jumps unconditionally past the `throw`, allowing managers to decide on requests from any department:
  ```java
  if (context.shouldMutate(id)) {
      // Pop the boolean result of Long.equals off the stack and jump past the throw
      mv.visitInsn(Opcodes.POP);
      mv.visitJumpInsn(Opcodes.GOTO, label);
      return;
  }
  ```

### Custom Mutator 2 — `SWAP_APPROVER_ROLE` (BR3 / BR4)
Source: [`SwapApproverRoleMutator.java`](../../tools/pit-custom-mutators/src/main/java/com/sandy/pit/SwapApproverRoleMutator.java#L15-L61).

- **Target production rule** (`RequestStatus.java:21-27`):
  ```java
  public Role approverRole() {
      return switch (this) {
          case SUBMITTED -> Role.MANAGER;
          case MANAGER_APPROVED -> Role.FINANCE;
          default -> null;
      };
  }
  ```
- **What the mutator does**: Inside `approverRole()`, it intercepts `GETSTATIC` loads of `Role.MANAGER` and `Role.FINANCE` and swaps them (`MANAGER -> FINANCE` and `FINANCE -> MANAGER`), inverting stage ownership between BR2/BR3 and BR4:
  ```java
  if ("MANAGER".equals(name)) {
      MutationIdentifier id = context.registerMutation(
              SwapApproverRoleMutator.this,
              "BR3/BR4 custom mutator: swapped Role.MANAGER to Role.FINANCE in approverRole");
      if (context.shouldMutate(id)) {
          super.visitFieldInsn(opcode, owner, "FINANCE", descriptor);
          return;
      }
  } else if ("FINANCE".equals(name)) {
      ...
          super.visitFieldInsn(opcode, owner, "MANAGER", descriptor);
  ```

---

## 4. Baseline vs Extended Mutation Runs (Before Adding Tests)

All runs below executed strictly against the initial 75 team white-box tests (`*WhiteBoxTest`):

| Run | Mutator Group(s) | Generated | Killed | Survived | No Coverage | Mutation Score | Evidence |
|---|---|---:|---:|---:|---:|---:|---|
| **Reported Baseline** | `DEFAULTS` | 79 | 71 | 8 | 0 | **90%** | [`07_pit_baseline_run.txt`](evidence/07_pit_baseline_run.txt), [`pit-baseline/mutations.xml`](evidence/pit-baseline/mutations.xml) |
| **Baseline + Custom** | `DEFAULTS`, `DROP_DEPARTMENT_CHECK`, `SWAP_APPROVER_ROLE` | 82 | 74 | 8 | 0 | **90%** | [`07_pit_defaults_custom_run.txt`](evidence/07_pit_defaults_custom_run.txt), [`pit-defaults-custom/mutations.xml`](evidence/pit-defaults-custom/mutations.xml) |
| **Stronger + Custom** | `STRONGER`, `DROP_DEPARTMENT_CHECK`, `SWAP_APPROVER_ROLE` | 108 | 100 | 8 | 0 | **93%** | [`07_pit_stronger_custom_run.txt`](evidence/07_pit_stronger_custom_run.txt), [`pit-stronger-custom/mutations.xml`](evidence/pit-stronger-custom/mutations.xml) |
| **Extended (`ALL` + Custom)** | `ALL`, `DROP_DEPARTMENT_CHECK`, `SWAP_APPROVER_ROLE` | 333 | 312 | 19 | 2 | **94%** | [`07_pit_all_custom_run.txt`](evidence/07_pit_all_custom_run.txt), [`pit-all-custom/mutations.xml`](evidence/pit-all-custom/mutations.xml) |

- **Why `DEFAULTS` stays the reported baseline (90%)**: PIT's `DEFAULTS` group is the standard benchmark across projects; our custom mutators added 3 business-rule mutations (`DROP_DEPARTMENT_CHECK`: 1/1 killed; `SWAP_APPROVER_ROLE`: 2/2 killed), leaving the score at 74/82 (90%).
- **Why the extended `ALL + custom` run was executed**: Both `DEFAULTS` and `STRONGER` produced only **8 surviving mutants** (all `VoidMethodCallMutator` setter removals), because our initial 75 white-box tests already killed 100% of `NegateConditionals`, `RemoveConditional`, `SwitchMutator`, and `NullReturnVals` mutants. Running PIT's full `ALL` group adds `NonVoidMethodCallMutator` (getter/argument omissions) and `ConstructorCallMutator`, exposing **21 non-killed mutants (19 `SURVIVED` + 2 `NO_COVERAGE`)** so we can classify and eliminate >= 15 real survivors.

---

## 5. Classification of All 21 Non-Killed Mutants (`ALL` + Custom, Before Fix)

Every non-killed mutant from [`evidence/pit-all-custom/mutations.xml`](evidence/pit-all-custom/mutations.xml):

| # | Class & Method | Line | PIT Status | Mutator | Mutation Description | Classification | Reason |
|---:|---|---:|---|---|---|---|---|
| 1 | `ExpenseService.list` | 82 | `NO_COVERAGE` | `ConstructorCallMutator` | removed call to `java/lang/MatchException::<init>` | **Equivalent in practice** | `javac` adds an unreachable default branch for the enum switch (`switch (me.getRole())` over the 3-constant `Role` enum). |
| 2 | `ExpenseService.assertCanView` | 187 | `NO_COVERAGE` | `ConstructorCallMutator` | removed call to `java/lang/MatchException::<init>` | **Equivalent in practice** | `javac` adds an unreachable default branch for the enum switch (`switch (me.getRole())` over the 3-constant `Role` enum). |
| 3 | `ExpenseService.create` | 53 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `ExpenseRequest::setStatus` | **Equivalent** | `ExpenseRequest.java:69` already initializes `private RequestStatus status = RequestStatus.DRAFT;`, making `setStatus(DRAFT)` a semantic no-op on a new object. |
| 4 | `ExpenseService.get` | 95 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `java/util/List::size` | **Equivalent in practice** | `RequestDetail.of(r)` already reads both lists inside the same transaction, so removing `r.getItems().size()` does not change observable behaviour. |
| 5 | `ExpenseService.get` | 96 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `java/util/List::size` | **Equivalent in practice** | `RequestDetail.of(r)` already reads both lists inside the same transaction, so removing `r.getApprovals().size()` does not change observable behaviour. |
| 6 | `ExpenseService.create` | 50 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `CreateRequest::title` | **Weak assertion** | Existing `create_*` tests asserted currency, description, status, and totalAmount, but never `d.title()`. |
| 7 | `ExpenseService.create` | 50 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `ExpenseRequest::setTitle` | **Weak assertion** | Same root cause: `d.title()` was never asserted in `create_*` tests (only in `update_*`). |
| 8 | `ExpenseService.toItem` | 64 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `ItemInput::description` | **Weak assertion** | Existing `create_*`/`update_*` tests verified item `amount` and count, never `item.description()`. |
| 9 | `ExpenseService.toItem` | 64 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `ExpenseItem::setDescription` | **Weak assertion** | Same root cause: `item.description()` was never asserted on returned items. |
| 10 | `ExpenseService.toItem` | 65 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `ItemInput::category` | **Weak assertion** | Existing `create_*`/`update_*` tests never asserted `item.category()`. |
| 11 | `ExpenseService.toItem` | 65 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `ExpenseItem::setCategory` | **Weak assertion** | Same root cause: `item.category()` was never asserted on returned items. |
| 12 | `ExpenseService.toItem` | 70 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `ItemInput::incurredOn` | **Weak assertion** | Existing `create_*`/`update_*` tests never asserted `item.incurredOn()`. |
| 13 | `ExpenseService.toItem` | 70 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `ExpenseItem::setIncurredOn` | **Weak assertion** | Same root cause: `item.incurredOn()` was never asserted on returned items. |
| 14 | `ExpenseService.transition` | 199 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `Approval::setRequest` | **Weak assertion** | Approval tests checked `action`, `fromStatus`, `toStatus`, `actor`, and `comment`, but never `a.getRequest()`. |
| 15 | `AuthService.register` | 56 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `RegisterRequest::email` | **Weak assertion** | `register_*` tests asserted `role`, `department`, `passwordHash`, and token, but never `saved.getEmail()` or `res.user().email()`. |
| 16 | `AuthService.register` | 56 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `User::setEmail` | **Weak assertion** | Same root cause: stored user email was omitted from assertions (note `existsByEmail` at line 45 read `req.email()` separately). |
| 17 | `AuthService.register` | 58 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `RegisterRequest::fullName` | **Weak assertion** | `register_*` tests never asserted `saved.getFullName()` or `res.user().fullName()`. |
| 18 | `AuthService.register` | 58 | `SURVIVED` | `VoidMethodCallMutator` | removed call to `User::setFullName` | **Weak assertion** | Same root cause: `fullName` on saved user and `UserView` was unasserted. |
| 19 | `AuthService.login` | 71 | `SURVIVED` | `ConstructorCallMutator` | removed call to `UsernamePasswordAuthenticationToken::<init>` | **Weak assertion** | `login_success_*` never verified `authManager.authenticate(...)` received a non-null `UsernamePasswordAuthenticationToken`. |
| 20 | `AuthService.login` | 71 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `LoginRequest::email` | **Weak assertion** | Mock `authManager.authenticate(...)` argument was not captured to assert principal equals `req.email()`. |
| 21 | `AuthService.login` | 71 | `SURVIVED` | `NonVoidMethodCallMutator` | removed call to `LoginRequest::password` | **Weak assertion** | Mock `authManager.authenticate(...)` argument was not captured to assert credentials equals `req.password()`. |

Summary: **1 Equivalent + 4 Equivalent in practice** mutants + **16 Weak-assertion killable** mutants (**21 total**, including **19 `SURVIVED`**).

---

## 6. Tests Added to Kill Survivors

Four targeted white-box tests were added without altering or weakening any existing test:

1. [`ExpenseServiceWhiteBoxTest.java#L121-L136`](../../tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java#L121-L136) (kills #6–#13):
   ```java
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
   ```

2. [`ExpenseServiceWhiteBoxTest.java#L483-L489`](../../tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java#L483-L489) (kills #14):
   ```java
   @Test
   void approve_setsApprovalRequestBackReference() {
       ExpenseRequest r = request(56L, alice, eng, RequestStatus.SUBMITTED);
       when(requests.findById(56L)).thenReturn(Optional.of(r));
       service.approve(principal(bob), 56L, "ok");
       assertThat(r.getApprovals().get(0).getRequest()).isSameAs(r);
   }
   ```

3. [`AuthServiceWhiteBoxTest.java#L105-L121`](../../tests/team/unit/com/sandy/expense/service/AuthServiceWhiteBoxTest.java#L105-L121) (kills #15–#18):
   ```java
   @Test
   void register_persistsEmailAndFullName() {
       when(users.existsByEmail("newuser@acme.com")).thenReturn(false);
       when(encoder.encode("password123")).thenReturn("hash");
       when(jwt.issue(any())).thenReturn("tok");
       when(jwt.ttlSeconds()).thenReturn(7200L);

       AuthResponse res =
               service.register(new RegisterRequest("newuser@acme.com", "password123", "New User", null));

       ArgumentCaptor<User> saved = ArgumentCaptor.forClass(User.class);
       verify(users).save(saved.capture());
       assertThat(saved.getValue().getEmail()).isEqualTo("newuser@acme.com");
       assertThat(saved.getValue().getFullName()).isEqualTo("New User");
       assertThat(res.user().email()).isEqualTo("newuser@acme.com");
       assertThat(res.user().fullName()).isEqualTo("New User");
   }
   ```

4. [`AuthServiceWhiteBoxTest.java#L159-L173`](../../tests/team/unit/com/sandy/expense/service/AuthServiceWhiteBoxTest.java#L159-L173) (kills #19–#21):
   ```java
   @Test
   void login_passesEmailAndPasswordToAuthenticationManager() {
       User u = user(6L, "login@acme.com", Role.EMPLOYEE);
       when(users.findByEmail("login@acme.com")).thenReturn(Optional.of(u));
       when(jwt.issue(u)).thenReturn("tok");
       when(jwt.ttlSeconds()).thenReturn(60L);

       service.login(new LoginRequest("login@acme.com", "secret-pw"));

       ArgumentCaptor<Authentication> authCap = ArgumentCaptor.forClass(Authentication.class);
       verify(authManager).authenticate(authCap.capture());
       assertThat(authCap.getValue()).isInstanceOf(UsernamePasswordAuthenticationToken.class);
       assertThat(authCap.getValue().getPrincipal()).isEqualTo("login@acme.com");
       assertThat(authCap.getValue().getCredentials()).isEqualTo("secret-pw");
   }
   ```

---

## 7. Before vs After Scores

| Configuration | Before | After | Remaining Non-Killed | Evidence |
|---|---:|---:|---|---|
| **`DEFAULTS` + Custom** (`pom.xml` default) | **74 / 82 (90%)** | **81 / 82 (99%)** | 1 Equivalent (`setStatus` at `ExpenseService.java:53`) | [`07_pit_defaults_custom_after_run.txt`](evidence/07_pit_defaults_custom_after_run.txt), [`pit-defaults-custom-after/mutations.xml`](evidence/pit-defaults-custom-after/mutations.xml) |
| **`ALL` + Custom** (extended) | **312 / 333 (94%)** | **328 / 333 (98%, 99% strength)** | 1 Equivalent (`setStatus`) + 4 Equivalent in practice (`List::size` x2, `MatchException` x2) | [`07_pit_all_custom_after_run.txt`](evidence/07_pit_all_custom_after_run.txt), [`pit-all-custom-after/mutations.xml`](evidence/pit-all-custom-after/mutations.xml) |

Team unit suite after additions: **79 tests, 0 failures, 0 errors**, JaCoCo check passing (**100%** line and branch coverage on all 4 scoped classes).

### Justified CI Threshold (`mutationThreshold`)
From the measured post-fix `DEFAULTS` + custom score of **99%** (81/82, where the single remaining mutant is mathematically equivalent) and before-fix baseline of **90%**, a CI `<mutationThreshold>95</mutationThreshold>` catches any newly unasserted branch or weakened assertion while tolerating minor equivalent setter mutations.
