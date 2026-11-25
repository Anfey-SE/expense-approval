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

Nodes represent maximal straight-line code sequences and individual short-circuit branch predicates; edges represent flow of control. All `throw` and normal `return` exits terminate at a single collapsed `[EXIT]` node (standard single-entry, single-exit CFG).

```
N1 ───────────────────────────────────────────────────────
   needed = r.getStatus().approverRole();      (line 167)
   Test D1: needed == null ?                   (line 168)
──────────────────────────────────────────────────────────
         │ true                           │ false
         ▼                                ▼
N2: throw NOT_PENDING (line 169)     N3: Test D2: me.getRole() != needed ?  (line 171)
         │                                │ true                 │ false
         │                                ▼                      ▼
         │                           N4: throw 403          N5a: Test D3-A: needed == Role.MANAGER ? (line 174)
         │                                │                      │ true                 │ false (short-circuit)
         │                                │                      ▼                      │
         │                                │                 N5b: Test D3-B: !dept.equals(myDept) ? (line 174)
         │                                │                      │ true        │ false  │
         │                                │                      ▼             ▼        ▼
         │                                │                 N6: throw 403     N7: Test D4: requester == me ? (line 177)
         │                                │                      │             │ true        │ false
         │                                │                      │             ▼             ▼
         │                                │                      │        N8: throw 403    N9: return (line 180)
         │                                │                      │             │             │
         └────────────────────────────────┴──────────────────────┴─────────────┴─────────────┘
                                                                 │
                                                                 ▼
                                                              [EXIT]
```

### Node and Edge Inventory

| Node | Description | Lines |
|---|---|---|
| N1 | Entry: compute `needed`; test D1 (`needed == null`) | 167–168 |
| N2 | Throw `NOT_PENDING` | 169 |
| N3 | Test D2 (`me.getRole() != needed`) | 171 |
| N4 | Throw role-mismatch 403 | 172 |
| N5a | Test D3-A (`needed == Role.MANAGER`) — left side of `&&` | 174 |
| N5b | Test D3-B (`!r.getDepartment().getId().equals(me.getDepartmentId())`) — right side of `&&` | 174 |
| N6 | Throw dept-mismatch 403 | 175 |
| N7 | Test D4 (`r.getRequester().getId().equals(me.getUserId())`) | 177 |
| N8 | Throw self-decision 403 | 178 |
| N9 | Normal return (fall-through) | 180 |
| EXIT | Collapsed terminal exit node (target of all throws and normal return) | — |

Edges (directed, source → target):

| # | From | To | Condition / Flow |
|---|---|---|---|
| e1 | N1 | N2 | D1 true (`needed == null`) |
| e2 | N1 | N3 | D1 false (`needed != null`) |
| e3 | N3 | N4 | D2 true (`me.getRole() != needed`) |
| e4 | N3 | N5a | D2 false (`me.getRole() == needed`) |
| e5 | N5a | N5b | D3-A true (`needed == Role.MANAGER`) |
| e6 | N5a | N7 | D3-A false (short-circuit `&&`, `needed != Role.MANAGER`) |
| e7 | N5b | N6 | D3-B true (`!dept.equals(myDept)`) |
| e8 | N5b | N7 | D3-B false (`dept.equals(myDept)`) |
| e9 | N7 | N8 | D4 true (`requester == me`) |
| e10 | N7 | N9 | D4 false (`requester != me`) |
| e11 | N2 | EXIT | exception exit (409 `NOT_PENDING`) |
| e12 | N4 | EXIT | exception exit (403 wrong role) |
| e13 | N6 | EXIT | exception exit (403 wrong department) |
| e14 | N8 | EXIT | exception exit (403 self-decision) |
| e15 | N9 | EXIT | normal return |

**N = 11 nodes, E = 15 edges.**

## 3. Cyclomatic Complexity — Step-by-Step

### Method 1: V(G) = E − N + 2

For a single-entry, single-exit connected CFG (1 component, $P = 1$):

```
E = 15  (edges e1..e15 listed above)
N = 11  (nodes N1..N9 + EXIT listed above)
V(G) = E − N + 2 = 15 − 11 + 2 = 6
```

### Method 2: Decisions + 1 (McCabe's shortcut)

Count every binary decision point in the method. McCabe's rule: each `if` counts +1, and each additional boolean operator (`&&`, `||`) in a compound predicate also counts +1.

| # | Decision point | Line | +N |
|---|---|---|---|
| — | Base (every method starts at 1) | — | 1 |
| D1 | `if (needed == null)` | 168 | +1 |
| D2 | `if (me.getRole() != needed)` | 171 | +1 |
| D3-if | `if (needed == Role.MANAGER && ...)` | 174 | +1 |
| D3-&& | `&&` operator in D3 | 174 | +1 |
| D4 | `if (r.getRequester().getId().equals(me.getUserId()))` | 177 | +1 |

```
V(G) = 1 + 4 ifs + 1 && = 6
```

### Reconciliation

Both methods give **V(G) = 6**:
- `E − N + 2` (single-entry, single-exit CFG with short-circuit `&&` expanded): `15 − 11 + 2 = 6` ✓
- `1 + decisions` (4 `if` statements + 1 `&&` operator): `1 + 4 + 1 = 6` ✓

> [!NOTE]
> SonarQube Community Build 26.11.0.134175 does **not** expose per-method cyclomatic or cognitive complexity via the UI or REST API (`api/measures/component` returns file-level aggregates only). For `ExpenseService.java` as a whole (14 functions), SonarQube reports **cyclomatic complexity = 45** and **cognitive complexity = 22**. The value **V(G) = 6** for `assertCanDecide` is therefore our hand calculation verified by both CFG and predicate-counting formulas.

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
