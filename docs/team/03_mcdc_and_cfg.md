# Task 4 — CFG, Cyclomatic Complexity, MCC, and MC/DC for `assertCanDecide`

All source references are to `src/main/java/com/sandy/expense/service/ExpenseService.java`.

## 1. Source Code Under Analysis (verbatim, lines 162–180)

```java
/**
 * Whoever decides on a request must (1) hold the role that owns the request's current stage,
 * (2) for a MANAGER, be in the same department, and (3) never be the requester themselves.
 */
private void assertCanDecide(AppUserPrincipal me, ExpenseRequest r) {  // line 166
    Role needed = r.getStatus().approverRole();                         // line 167
    if (needed == null) {                                               // line 168
        throw ApiException.conflict("NOT_PENDING", "This request is not awaiting a decision"); // line 169
    }
    if (me.getRole() != needed) {                                       // line 171
        throw ApiException.forbidden("This stage must be decided by a " + needed); // line 172
    }
    if (needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())) { // line 174
        throw ApiException.forbidden("You can only decide on requests in your own department"); // line 175
    }
    if (r.getRequester().getId().equals(me.getUserId())) {              // line 177
        throw ApiException.forbidden("You cannot decide on your own request"); // line 178
    }
}                                                                        // line 180
```

## 2. Control-Flow Graph (CFG)

Nodes represent maximal straight-line code sequences; edges represent flow of control.

```
N1 ──────────────────────────────────────────────
   needed = r.getStatus().approverRole();         (line 167)
   Test: needed == null ?                          (line 168)
─────────────────────────────────────────────────
         │ true                   │ false
         ▼                        ▼
N2: throw NOT_PENDING          N3: Test: me.getRole() != needed ?  (line 171)
         │                             │ true             │ false
         ▼ (exit)                      ▼                  ▼
      [EXIT-1]                  N4: throw 403         N5: Test: needed==MANAGER
                                         │                  && !dept.equals(myDept) ?
                                         ▼ (exit)                 (line 174)
                                      [EXIT-2]          │ true             │ false
                                                         ▼                  ▼
                                                   N6: throw 403       N7: Test: requester==me ?
                                                         │                       (line 177)
                                                         ▼ (exit)      │ true        │ false
                                                      [EXIT-3]          ▼             ▼
                                                                  N8: throw 403    N9: return (fall-through)
                                                                        │                │
                                                                        ▼ (exit)         ▼ (exit)
                                                                     [EXIT-4]         [EXIT-5]
```

### Node and Edge Inventory

| Node | Description | Lines |
|---|---|---|
| N1 | Entry: compute `needed`; test `needed == null` | 167–168 |
| N2 | Throw `NOT_PENDING` | 169 |
| N3 | Test `me.getRole() != needed` | 171 |
| N4 | Throw role-mismatch 403 | 172 |
| N5 | Test compound: `needed == Role.MANAGER && !dept.equals(myDept)` | 174 |
| N6 | Throw dept-mismatch 403 | 175 |
| N7 | Test `requester.getId().equals(me.getUserId())` | 177 |
| N8 | Throw self-decision 403 | 178 |
| N9 | Normal return (fall-through) | 180 |

Edges (directed, source → target):

| # | From | To | Condition |
|---|---|---|---|
| e1 | N1 | N2 | `needed == null` is true |
| e2 | N1 | N3 | `needed == null` is false |
| e3 | N3 | N4 | `me.getRole() != needed` is true |
| e4 | N3 | N5 | `me.getRole() != needed` is false |
| e5 | N5 | N6 | compound D3 is true |
| e6 | N5 | N7 | compound D3 is false |
| e7 | N7 | N8 | `requester.getId().equals(me.getUserId())` is true |
| e8 | N7 | N9 | `requester.getId().equals(me.getUserId())` is false |

**N = 9 nodes, E = 8 edges** (each throw/return is a unique exit node with no outgoing edges).

## 3. Cyclomatic Complexity — Step-by-Step

### Method 1: V(G) = E − N + 2

```
E = 8   (edges listed above)
N = 9   (nodes listed above)
V(G) = 8 − 9 + 2 = 1
```

Wait — this gives 1, which is the base case with no decisions. The formula `E − N + 2` applies to a **connected** graph with a single entry and single exit. Here there are **5 exit nodes** (N2, N4, N6, N8, N9). Using the standard formulation for a graph with multiple exits, we add one edge from each exit back to the entry to close the graph, giving:

```
E_closed = 8 + 5 (back-edges from each exit to N1) = 13
N_closed = 9
V(G) = E_closed − N_closed + 2 = 13 − 9 + 2 = 6
```

> [!NOTE]
> Alternatively, treat the method as one connected region by counting only the **number of linearly independent paths**. The correct answer is **5**, matching decisions+1 below, because the standard `E − N + 2` with a single exit is equivalent.

### Method 2: Decisions + 1 (McCabe's shortcut)

Count every binary decision (predicate) in the method:

| # | Predicate | Line |
|---|---|---|
| D1 | `needed == null` | 168 |
| D2 | `me.getRole() != needed` | 171 |
| D3 | `needed == Role.MANAGER && !r.getDepartment().getId().equals(me.getDepartmentId())` | 174 |
| D4 | `r.getRequester().getId().equals(me.getUserId())` | 177 |

D3 is a **compound predicate** (two conditions: A = `needed == Role.MANAGER`, B = `!dept.equals(myDept)`) joined by `&&`. McCabe counts it as one decision; MC/DC treats A and B as independent conditions.

```
V(G) = decisions + 1 = 4 + 1 = 5
```

### Reconciliation

The two methods agree when the graph is treated as a single-entry, single-exit (SESE) region. The correct **cyclomatic complexity is 5**: there are 4 binary decisions, giving 5 linearly independent paths through the method (one for each exit point). The `E − N + 2` with the standard multi-exit treatment above gives 6 because it counts the closed graph; the **McCabe shortcut (5) is the authoritative figure** cited in test/coverage planning.

> [!NOTE]
> SonarQube cognitive complexity counts the nesting depth in addition to the number of decisions, so it typically reports a **higher** number than McCabe cyclomatic for deeply nested code. `assertCanDecide` is flat (no nesting), so both metrics agree at approximately 5. The exact SonarQube cyclomatic figure will be recorded once the SonarQube scan is run in Task 5.

## 4. Conditions (D1–D4) and Labels

| Label | Condition | Location |
|---|---|---|
| D1 | `needed == null` | Line 168 — `needed` is null for DRAFT, FINANCE_APPROVED, REJECTED |
| D2 | `me.getRole() != needed` | Line 171 — role mismatch (e.g. EMPLOYEE when MANAGER needed) |
| A (part of D3) | `needed == Role.MANAGER` | Line 174 (left side of `&&`) |
| B (part of D3) | `!r.getDepartment().getId().equals(me.getDepartmentId())` | Line 174 (right side of `&&`) |
| D4 | `r.getRequester().getId().equals(me.getUserId())` | Line 177 — self-decision |

## 5. Full MCC (Multiple Condition Coverage) Table

For MCC, every combination of truth values for each individual condition must be exercised. D3 has two sub-conditions (A and B), so we need 2⁴ = 16 entries for the full Cartesian product of D1 × D2 × A × B × D4.

However, short-circuit evaluation (`&&` in D3, sequential `if` chain) means many combinations are logically infeasible (unreachable at runtime):

| Row | D1 | D2 | A | B | D4 | Outcome | Feasible? | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | T | — | — | — | — | NOT_PENDING | ✓ | D1 true → exit N2; D2/A/B/D4 not evaluated |
| 2 | F | T | — | — | — | Role 403 | ✓ | D2 true → exit N4 |
| 3 | F | F | T | T | — | Dept 403 | ✓ | D3=A∧¬B… wait, B is "not equal", so B=T means different dept → D3=T |
| 4 | F | F | T | F | T | Self 403 | ✓ | D3=F (A=T,B=F→same dept), D4=T |
| 5 | F | F | T | F | F | Allow | ✓ | D3=F, D4=F → normal return |
| 6 | F | F | F | — | T | Self 403 | ✓ | A=F (FINANCE) → D3 short-circuits to false; D4=T |
| 7 | F | F | F | — | F | Allow | ✓ | A=F, D4=F → normal return |
| 8 | F | F | T | — | — | — | Infeasible | A=T means needed=MANAGER; D2=F means me.role=MANAGER; B must be evaluated |
| — | F | F | F | T | — | — | Infeasible | A=F short-circuits; B is never read |

> [!NOTE]
> Row 8 collapses: when A=T the B column is always reachable. Rows 3–5 cover A=T. Rows 6–7 cover A=F. Row 2 (D2=T) means me.role≠needed, so if needed=null (D1=F), role mismatch exits at N4 before reaching D3.

**Feasible combinations**: rows 1, 2, 3, 4, 5, 6, 7 → **7 distinct feasible MCC test cases**.

## 6. MC/DC Independence Pairs

MC/DC requires that for each condition, there is a pair of tests where **that condition alone changes the overall decision**, while all other conditions are held constant.

### D1: `needed == null`

| Condition value | D1 | D2 | A | B | D4 | Outcome |
|---|---|---|---|---|---|---|
| Pair D1-α | **T** | — | — | — | — | NOT_PENDING |
| Pair D1-β | **F** | F | F | — | F | Allow |

D1 changes T→F; D2, A, B, D4 do not influence (or are held constant at non-triggering values). Outcome changes: blocked → allowed.

**Test methods:**
- D1-α (needed=null): `approve_statusAwaitingNobody_isNotPending_D1` (line 379, parameterized with DRAFT/FINANCE_APPROVED/REJECTED) and `reject_statusAwaitingNobody_isNotPending_D1` (line 394)
- D1-β (needed≠null, reaches normal return): `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431) — FINANCE on MANAGER_APPROVED, no self-decision → allowed

### D2: `me.getRole() != needed`

| Condition value | D1 | D2 | A | B | D4 | Outcome |
|---|---|---|---|---|---|---|
| Pair D2-α | F | **T** | — | — | — | Role 403 |
| Pair D2-β | F | **F** | F | — | F | Allow |

D2 changes T→F; D1 is false (stage is pending); other conditions held at non-triggering values.

**Test methods:**
- D2-α (role mismatch): `approve_employeeOnSubmitted_wrongRole_D2` (line 411) — EMPLOYEE on SUBMITTED (needs MANAGER) and `approve_managerOnManagerApproved_wrongRole_D2` (line 420) — MANAGER on MANAGER_APPROVED (needs FINANCE)
- D2-β (role matches): `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431) — FINANCE on MANAGER_APPROVED with correct role

### Condition A: `needed == Role.MANAGER` (left side of D3)

| Condition value | D1 | D2 | A | B | D4 | D3 outcome | Method outcome |
|---|---|---|---|---|---|---|---|
| Pair A-α | F | F | **T** | T | — | True | Dept 403 |
| Pair A-β | F | F | **F** | — | F | False (short-circuit) | Allow |

A changes T→F; D1=F (pending), D2=F (role matches), D4=F (not self). When A=T and B=T → D3=T → 403. When A=F → D3=F regardless of B → reaches D4.

**Test methods:**
- A-α (A=T, B=T → D3=T): `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441)
- A-β (A=F → D3 short-circuits): `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431)

### Condition B: `!r.getDepartment().getId().equals(me.getDepartmentId())` (right side of D3)

| Condition value | D1 | D2 | A | B | D4 | D3 outcome | Method outcome |
|---|---|---|---|---|---|---|---|
| Pair B-α | F | F | T | **T** | — | True | Dept 403 |
| Pair B-β | F | F | T | **F** | F | False | Allow |

A must be T in both (so B is evaluated); B changes T→F. B=T means different department; B=F means same department. D4=F (not self) in both.

**Test methods:**
- B-α (B=T, different dept): `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` (line 441)
- B-β (B=F, same dept): `approve_managerSameDepartment_isAllowed_D3_BtoFalse` (line 453)

### D4: `r.getRequester().getId().equals(me.getUserId())`

| Condition value | D1 | D2 | A | B | D4 | Outcome |
|---|---|---|---|---|---|---|
| Pair D4-α | F | F | F | — | **T** | Self 403 |
| Pair D4-β | F | F | F | — | **F** | Allow |

D4 changes T→F; D1=F, D2=F (role matches), A=F (FINANCE, so B not evaluated), keeping D3=F.

**Test methods:**
- D4-α (D4=T, MANAGER self): `approve_managerOnOwnRequest_isForbidden_D4_true` (line 479)
- D4-α (D4=T, FINANCE self): `approve_financeOnOwnRequest_isForbidden_D4_true` (line 490)
- D4-β (D4=F): `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` (line 431)

### MC/DC Independence Pairs Summary Table

| Condition | True-case test method(s) | False-case test method(s) |
|---|---|---|
| D1 (`needed==null`) | `approve_statusAwaitingNobody_isNotPending_D1` (×3 statuses) | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |
| D2 (`role mismatch`) | `approve_employeeOnSubmitted_wrongRole_D2`, `approve_managerOnManagerApproved_wrongRole_D2` | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |
| A (`needed==MANAGER`) | `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |
| B (`!dept.equals(myDept)`) | `approve_managerOtherDepartment_isForbidden_D3_BtoTrue` | `approve_managerSameDepartment_isAllowed_D3_BtoFalse` |
| D4 (`self-decision`) | `approve_managerOnOwnRequest_isForbidden_D4_true`, `approve_financeOnOwnRequest_isForbidden_D4_true` | `approve_financeOnRequestFromAnotherDepartment_isAllowed_D3_A_false` |

All test methods above are in `tests/team/unit/com/sandy/expense/service/ExpenseServiceWhiteBoxTest.java`.

## 7. Decision Table for BR2 (`assertCanDecide`)

| D1: needed=null | D2: role≠needed | A: needed=MGR | B: diff dept | D4: self | Decision | Error code |
|---|---|---|---|---|---|---|
| T | — | — | — | — | Reject | `NOT_PENDING` |
| F | T | — | — | — | Reject | (forbidden: "stage must be decided by…") |
| F | F | T | T | — | Reject | (forbidden: "own department") |
| F | F | T | F | T | Reject | (forbidden: "own request") |
| F | F | T | F | F | **Allow** | — |
| F | F | F | — | T | Reject | (forbidden: "own request") |
| F | F | F | — | F | **Allow** | — |

(— = not evaluated due to short-circuit or irrelevance)

## 8. Decision Table for BR4 (Finance acts only on MANAGER_APPROVED)

BR4 is derived from BR2 + the state machine. The table shows `assertCanDecide` outcomes for a FINANCE approver against each request state:

| Request status | `approverRole()` | D1 (needed=null) | D2 for FINANCE | D3 | Outcome |
|---|---|---|---|---|---|
| DRAFT | null | T | — | — | Reject: `NOT_PENDING` |
| SUBMITTED | MANAGER | F | T (FINANCE≠MANAGER) | — | Reject: role mismatch |
| MANAGER_APPROVED | FINANCE | F | F | F (A=false→skip) | Allow (if D4=F) |
| FINANCE_APPROVED | null | T | — | — | Reject: `NOT_PENDING` |
| REJECTED | null | T | — | — | Reject: `NOT_PENDING` |

Finance can **only** successfully act when the status is MANAGER_APPROVED. All other states are rejected before reaching D3 or D4.

## 9. State Transition Table for BR3

Source: `domain/RequestStatus.java` lines 13–36 and `service/ExpenseService.java` lines 127–158.

### Allowed Transitions

| From state | Action | Actor constraint | To state | Source method |
|---|---|---|---|---|
| DRAFT | submit | Requester only, ≥1 item | SUBMITTED | `ExpenseService.submit` (line 127) |
| SUBMITTED | approve | MANAGER, same dept, not self | MANAGER_APPROVED | `ExpenseService.approve` (line 143) |
| SUBMITTED | reject | MANAGER, same dept, not self | REJECTED | `ExpenseService.reject` (line 152) |
| MANAGER_APPROVED | approve | FINANCE, not self | FINANCE_APPROVED | `ExpenseService.approve` (line 143) |
| MANAGER_APPROVED | reject | FINANCE, not self | REJECTED | `ExpenseService.reject` (line 152) |

FINANCE_APPROVED and REJECTED are **terminal** — `approverRole()` returns null for both; any attempt to approve or reject them throws `NOT_PENDING`.

### Disallowed Transitions (at least one per state)

| From state | Attempted action | Why rejected | Error code / status |
|---|---|---|---|
| DRAFT | approve | `needed == null` (D1=T) | `NOT_PENDING` / 409 |
| DRAFT | submit (not owner) | `!requester.equals(me)` | 403 |
| DRAFT | submit (no items) | `items.isEmpty()` | `EMPTY_REQUEST` / 400 |
| SUBMITTED | approve by EMPLOYEE | `me.role != MANAGER` (D2=T) | 403 |
| SUBMITTED | approve by MANAGER (wrong dept) | D3=T | 403 |
| SUBMITTED | approve by MANAGER (self) | D4=T | 403 |
| SUBMITTED | submit again | `status != DRAFT` | `NOT_SUBMITTABLE` / 409 |
| MANAGER_APPROVED | approve by MANAGER | `me.role != FINANCE` (D2=T) | 403 |
| FINANCE_APPROVED | approve | `needed == null` (D1=T) | `NOT_PENDING` / 409 |
| REJECTED | reject again | `needed == null` (D1=T) | `NOT_PENDING` / 409 |

### State Transition Matrix

```
                     submit    approve(MGR)    approve(FIN)    reject(MGR/FIN)
DRAFT                → SUBMITTED   ✗               ✗               ✗
SUBMITTED            ✗           → MGR_APR        ✗           → REJECTED
MANAGER_APPROVED     ✗               ✗         → FIN_APR      → REJECTED
FINANCE_APPROVED     ✗               ✗               ✗               ✗
REJECTED             ✗               ✗               ✗               ✗
```

(✗ = `NOT_PENDING`, role-mismatch 403, or `NOT_SUBMITTABLE` depending on the from-state)
