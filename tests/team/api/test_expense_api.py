"""
API & Integration Test Suite (Member 2 — 24i-3097).

Covers:
1. Generated EP & 3-point BVA tests from OpenAPI spec (one invalid value per test).
2. Business rules BR1-BR4 rejections and boundary enforcement.
3. State transition matrix (every allowed transition + disallowed transitions from every state).
4. Idempotency: separate tests for double-submit, double-manager-approve, double-finance-approve,
   double-reject, and concurrent double-approve (threading.Barrier), each asserting exactly one
   new trail row per successful transition and no extra rows on the rejected repeat.
5. Cross-workflow read-back assertions after both success and rejection.
6. Endpoint behavior / weakness verification (pagination clamping, blank rejection comment, unauthenticated access).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest
import requests

from conftest import (
    BASE_URL,
    DATA_FILE,
    auth_headers,
    create_draft,
    submit_request,
    valid_item,
    valid_request_payload,
)


def _load_cases() -> dict[str, Any]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


_DATA = _load_cases()


def _collect_create_request_cases() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for c in _DATA["ep_cases"].get("CreateRequest", []):
        if c["field"] == "items":
            continue  # array count tested in BVA
        cases.append((f"EP:CreateRequest.{c['field']}:{c['class']}", c))
    for c in _DATA["bva_cases"].get("CreateRequest", []):
        cases.append((f"BVA:CreateRequest.{c['field']}:{c['point']}", c))
    return cases


def _collect_item_input_cases() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for c in _DATA["ep_cases"].get("ItemInput", []):
        cases.append((f"EP:ItemInput.{c['field']}:{c['class']}", c))
    for c in _DATA["bva_cases"].get("ItemInput", []):
        cases.append((f"BVA:ItemInput.{c['field']}:{c['point']}", c))
    return cases


def _collect_decision_cases() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for c in _DATA["ep_cases"].get("DecisionInput", []):
        cases.append((f"EP:DecisionInput.{c['field']}:{c['class']}", c))
    for c in _DATA["bva_cases"].get("DecisionInput", []):
        cases.append((f"BVA:DecisionInput.{c['field']}:{c['point']}", c))
    return cases


# ---------------------------------------------------------------------------
# 1. Generated EP & 3-Point BVA Tests (CreateRequest, ItemInput, DecisionInput)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_id,case", _collect_create_request_cases(), ids=lambda x: x if isinstance(x, str) else "")
def test_create_request_ep_and_bva(tokens: dict[str, str], case_id: str, case: dict[str, Any]) -> None:
    """Test CreateRequest fields using generated EP & 3-point BVA values (one invalid value per test)."""
    field = case["field"]
    if field == "items":
        count = case["count"]
        payload = valid_request_payload(items=[valid_item(description=f"Item {i}") for i in range(count)])
    else:
        payload = valid_request_payload(**{field: case["value"]})

    resp = requests.post(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(tokens["alice"]),
        json=payload,
        timeout=15,
    )

    if case["valid"]:
        assert resp.status_code == 201, f"{case_id} expected 201, got {resp.status_code}: {resp.text}"
        created = resp.json()
        assert created["status"] == "DRAFT"
        # Read-back verification
        rb = requests.get(f"{BASE_URL}/api/requests/{created['id']}", headers=auth_headers(tokens["alice"]), timeout=10)
        assert rb.status_code == 200
        assert rb.json()["id"] == created["id"]
    else:
        assert resp.status_code == 400, f"{case_id} expected 400, got {resp.status_code}: {resp.text}"
        assert resp.json()["code"] in ("VALIDATION_ERROR", "MALFORMED_JSON")


@pytest.mark.parametrize("case_id,case", _collect_item_input_cases(), ids=lambda x: x if isinstance(x, str) else "")
def test_item_input_ep_and_bva(tokens: dict[str, str], case_id: str, case: dict[str, Any]) -> None:
    """Test ItemInput fields using generated EP & 3-point BVA values (one invalid value per test)."""
    field = case["field"]
    item = valid_item(**{field: case["value"]})
    payload = valid_request_payload(items=[item])

    resp = requests.post(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(tokens["alice"]),
        json=payload,
        timeout=10,
    )

    if case["valid"]:
        assert resp.status_code == 201, f"{case_id} expected 201, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert len(body["items"]) == 1
    else:
        assert resp.status_code == 400, f"{case_id} expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.parametrize("case_id,case", _collect_decision_cases(), ids=lambda x: x if isinstance(x, str) else "")
def test_decision_input_ep_and_bva(tokens: dict[str, str], case_id: str, case: dict[str, Any]) -> None:
    """Test DecisionInput.comment using generated EP & 3-point BVA values."""
    draft = create_draft(tokens["alice"])
    submit_request(tokens["alice"], draft["id"])

    resp = requests.post(
        f"{BASE_URL}/api/requests/{draft['id']}/approve",
        headers=auth_headers(tokens["bob"]),
        json={"comment": case["value"]},
        timeout=10,
    )

    if case["valid"]:
        assert resp.status_code == 200, f"{case_id} expected 200, got {resp.status_code}: {resp.text}"
        rb = requests.get(f"{BASE_URL}/api/requests/{draft['id']}", headers=auth_headers(tokens["bob"]), timeout=10)
        assert rb.status_code == 200
        assert rb.json()["status"] == "MANAGER_APPROVED"
    else:
        assert resp.status_code == 400, f"{case_id} expected 400, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 2. Query Parameter EP & BVA + Endpoint Weakness Checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status_val,expected_code", [
    ("DRAFT", 200),
    ("SUBMITTED", 200),
    ("MANAGER_APPROVED", 200),
    ("FINANCE_APPROVED", 200),
    ("REJECTED", 200),
    ("INVALID_STATUS", 400),
])
def test_list_status_filter_ep(tokens: dict[str, str], status_val: str, expected_code: int) -> None:
    resp = requests.get(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(tokens["alice"]),
        params={"status": status_val},
        timeout=10,
    )
    assert resp.status_code == expected_code


def test_list_pagination_clamping_weakness(tokens: dict[str, str]) -> None:
    """
    Documented endpoint weakness (EW-1): ExpenseController.list silently clamps
    negative page (-1 -> 0) and out-of-bounds size (0 -> 1, 101 -> 100)
    instead of returning HTTP 400 Bad Request as specified in the OpenAPI contract.
    """
    resp_neg = requests.get(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(tokens["alice"]),
        params={"page": -1, "size": 0},
        timeout=10,
    )
    assert resp_neg.status_code == 200
    assert resp_neg.json()["page"] == 0
    assert resp_neg.json()["size"] == 1

    resp_over = requests.get(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(tokens["alice"]),
        params={"page": 0, "size": 101},
        timeout=10,
    )
    assert resp_over.status_code == 200
    assert resp_over.json()["size"] == 100


# ---------------------------------------------------------------------------
# 3. Business Rules (BR1-BR4), State Transitions & Cross-Workflow Read-Backs
# ---------------------------------------------------------------------------


def test_full_happy_path_and_cross_workflow_readback(tokens: dict[str, str]) -> None:
    """Workflow 1 (Create -> Update -> Submit) + Workflow 2 (Manager Approve -> Finance Approve) with read-backs."""
    # Create draft
    draft = create_draft(tokens["alice"], valid_request_payload(currency="eur"))
    req_id = draft["id"]
    assert draft["status"] == "DRAFT"
    assert draft["currency"] == "EUR"
    assert draft["totalAmount"] == 25.50

    # Update draft (add 2 items)
    upd = requests.put(
        f"{BASE_URL}/api/requests/{req_id}",
        headers=auth_headers(tokens["alice"]),
        json=valid_request_payload(
            title="Updated Travel",
            currency=None,
            items=[valid_item(amount=40.00), valid_item(description="Taxi", category="Transport", amount=15.25)],
        ),
        timeout=10,
    )
    assert upd.status_code == 200
    assert upd.json()["totalAmount"] == 55.25

    # Workflow 1: Submit
    sub = submit_request(tokens["alice"], req_id)
    assert sub["status"] == "SUBMITTED"
    assert len(sub["approvals"]) == 1
    assert sub["approvals"][0]["action"] == "SUBMIT"

    # Workflow 2a: Manager Approve
    mgr = requests.post(
        f"{BASE_URL}/api/requests/{req_id}/approve",
        headers=auth_headers(tokens["bob"]),
        json={"comment": "Approved by Engineering Manager"},
        timeout=10,
    )
    assert mgr.status_code == 200
    assert mgr.json()["status"] == "MANAGER_APPROVED"

    # Workflow 2b: Finance Approve
    fin = requests.post(
        f"{BASE_URL}/api/requests/{req_id}/approve",
        headers=auth_headers(tokens["fiona"]),
        json={"comment": "Cleared for payout"},
        timeout=10,
    )
    assert fin.status_code == 200
    assert fin.json()["status"] == "FINANCE_APPROVED"

    # Final read-back as Employee
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["alice"]), timeout=10)
    assert rb.status_code == 200
    detail = rb.json()
    assert detail["status"] == "FINANCE_APPROVED"
    assert [a["action"] for a in detail["approvals"]] == ["SUBMIT", "APPROVE", "APPROVE"]
    assert [a["toStatus"] for a in detail["approvals"]] == ["SUBMITTED", "MANAGER_APPROVED", "FINANCE_APPROVED"]


def test_rejection_and_readback(tokens: dict[str, str]) -> None:
    """Manager rejects a SUBMITTED request; read-back verifies REJECTED status and approval trail."""
    draft = create_draft(tokens["alice"])
    req_id = draft["id"]
    submit_request(tokens["alice"], req_id)

    rej = requests.post(
        f"{BASE_URL}/api/requests/{req_id}/reject",
        headers=auth_headers(tokens["bob"]),
        json={"comment": "Missing receipt"},
        timeout=10,
    )
    assert rej.status_code == 200
    assert rej.json()["status"] == "REJECTED"

    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["alice"]), timeout=10)
    assert rb.status_code == 200
    assert rb.json()["status"] == "REJECTED"
    assert len(rb.json()["approvals"]) == 2
    assert rb.json()["approvals"][1]["action"] == "REJECT"
    assert rb.json()["approvals"][1]["comment"] == "Missing receipt"


def test_reject_without_comment_weakness(tokens: dict[str, str]) -> None:
    """
    Documented endpoint weakness (EW-2): POST /api/requests/{id}/reject accepts an empty
    or omitted comment without requiring a rejection reason.
    """
    draft = create_draft(tokens["alice"])
    submit_request(tokens["alice"], draft["id"])
    rej = requests.post(
        f"{BASE_URL}/api/requests/{draft['id']}/reject",
        headers=auth_headers(tokens["bob"]),
        timeout=10,
    )
    assert rej.status_code == 200
    assert rej.json()["status"] == "REJECTED"
    assert rej.json()["approvals"][-1]["comment"] == ""


def test_br2_and_br4_authorization_rejections(tokens: dict[str, str]) -> None:
    """BR2 & BR4: Wrong role, cross-department manager, and self-approval are all 403."""
    # Alice (Engineering) creates and submits
    draft = create_draft(tokens["alice"])
    req_id = draft["id"]
    submit_request(tokens["alice"], req_id)

    # Employee cannot approve
    r_emp = requests.post(f"{BASE_URL}/api/requests/{req_id}/approve", headers=auth_headers(tokens["alice"]), timeout=10)
    assert r_emp.status_code == 403

    # Cross-department manager (Dave, Sales) cannot approve Engineering request
    r_cross = requests.post(f"{BASE_URL}/api/requests/{req_id}/approve", headers=auth_headers(tokens["dave"]), timeout=10)
    assert r_cross.status_code == 403

    # Finance (Fiona) cannot approve before Manager (BR4)
    r_fin_early = requests.post(f"{BASE_URL}/api/requests/{req_id}/approve", headers=auth_headers(tokens["fiona"]), timeout=10)
    assert r_fin_early.status_code == 403

    # Cross-department read returns 404 (not 403, anti-enumeration)
    r_read_cross = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["dave"]), timeout=10)
    assert r_read_cross.status_code == 404

    # Manager (Bob) cannot approve his own submitted request (self-decision forbidden)
    bob_draft = create_draft(tokens["bob"])
    submit_request(tokens["bob"], bob_draft["id"])
    r_self = requests.post(f"{BASE_URL}/api/requests/{bob_draft['id']}/approve", headers=auth_headers(tokens["bob"]), timeout=10)
    assert r_self.status_code == 403

    # Read-back original request: still SUBMITTED, 1 approval row
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["alice"]), timeout=10)
    assert rb.json()["status"] == "SUBMITTED"
    assert len(rb.json()["approvals"]) == 1


def setup_request_in_state(tokens: dict[str, str], target_state: str) -> tuple[int, int]:
    """
    Creates and advances a fresh expense request to target_state.
    Returns (req_id, expected_approval_trail_count).
    """
    draft = create_draft(tokens["alice"])
    req_id = draft["id"]
    if target_state == "DRAFT":
        return req_id, 0

    submit_request(tokens["alice"], req_id)
    if target_state == "SUBMITTED":
        return req_id, 1

    if target_state == "MANAGER_APPROVED":
        res = requests.post(
            f"{BASE_URL}/api/requests/{req_id}/approve",
            headers=auth_headers(tokens["bob"]),
            json={"comment": "Manager approved"},
            timeout=10,
        )
        assert res.status_code == 200, f"Setup failed reaching MANAGER_APPROVED: {res.text}"
        return req_id, 2

    if target_state == "FINANCE_APPROVED":
        res1 = requests.post(
            f"{BASE_URL}/api/requests/{req_id}/approve",
            headers=auth_headers(tokens["bob"]),
            json={"comment": "Manager approved"},
            timeout=10,
        )
        assert res1.status_code == 200, f"Setup step 1 failed: {res1.text}"
        res2 = requests.post(
            f"{BASE_URL}/api/requests/{req_id}/approve",
            headers=auth_headers(tokens["fiona"]),
            json={"comment": "Finance approved"},
            timeout=10,
        )
        assert res2.status_code == 200, f"Setup step 2 failed reaching FINANCE_APPROVED: {res2.text}"
        return req_id, 3

    if target_state == "REJECTED":
        res = requests.post(
            f"{BASE_URL}/api/requests/{req_id}/reject",
            headers=auth_headers(tokens["bob"]),
            json={"comment": "Rejected by manager"},
            timeout=10,
        )
        assert res.status_code == 200, f"Setup failed reaching REJECTED: {res.text}"
        return req_id, 2

    raise ValueError(f"Unknown target state: {target_state}")


def dispatch_action(
    tokens: dict[str, str],
    req_id: int,
    action: str,
    actor_key: str,
    payload: dict[str, Any] | None = None,
) -> requests.Response:
    token = tokens[actor_key]
    if action == "submit":
        return requests.post(
            f"{BASE_URL}/api/requests/{req_id}/submit",
            headers=auth_headers(token),
            timeout=10,
        )
    if action == "approve":
        return requests.post(
            f"{BASE_URL}/api/requests/{req_id}/approve",
            headers=auth_headers(token),
            json=payload if payload is not None else {},
            timeout=10,
        )
    if action == "reject":
        return requests.post(
            f"{BASE_URL}/api/requests/{req_id}/reject",
            headers=auth_headers(token),
            json=payload if payload is not None else {},
            timeout=10,
        )
    if action == "update":
        return requests.put(
            f"{BASE_URL}/api/requests/{req_id}",
            headers=auth_headers(token),
            json=payload if payload is not None else valid_request_payload(),
            timeout=10,
        )
    raise ValueError(f"Unknown action: {action}")


ALLOWED_STATE_TRANSITIONS = [
    # (case_id, initial_state, action, actor_key, payload, expected_status, target_status, expected_trail_count, expected_last_action)
    (
        "DRAFT->SUBMITTED",
        "DRAFT",
        "submit",
        "alice",
        None,
        200,
        "SUBMITTED",
        1,
        "SUBMIT",
    ),
    (
        "SUBMITTED->MANAGER_APPROVED",
        "SUBMITTED",
        "approve",
        "bob",
        {"comment": "Approved by Manager"},
        200,
        "MANAGER_APPROVED",
        2,
        "APPROVE",
    ),
    (
        "SUBMITTED->REJECTED",
        "SUBMITTED",
        "reject",
        "bob",
        {"comment": "Rejected by Manager"},
        200,
        "REJECTED",
        2,
        "REJECT",
    ),
    (
        "MANAGER_APPROVED->FINANCE_APPROVED",
        "MANAGER_APPROVED",
        "approve",
        "fiona",
        {"comment": "Approved by Finance"},
        200,
        "FINANCE_APPROVED",
        3,
        "APPROVE",
    ),
    (
        "MANAGER_APPROVED->REJECTED",
        "MANAGER_APPROVED",
        "reject",
        "fiona",
        {"comment": "Rejected by Finance"},
        200,
        "REJECTED",
        3,
        "REJECT",
    ),
]


DISALLOWED_STATE_TRANSITIONS = [
    # (case_id, initial_state, action, actor_key, payload, expected_status, expected_state, expected_trail_count)
    ("DRAFT:approve_refused", "DRAFT", "approve", "bob", {"comment": "Premature"}, 409, "DRAFT", 0),
    ("DRAFT:reject_refused", "DRAFT", "reject", "bob", {"comment": "Premature"}, 409, "DRAFT", 0),
    ("DRAFT:non_owner_submit_refused", "DRAFT", "submit", "carol", None, 403, "DRAFT", 0),
    ("SUBMITTED:re_submit_refused", "SUBMITTED", "submit", "alice", None, 409, "SUBMITTED", 1),
    ("SUBMITTED:update_refused", "SUBMITTED", "update", "alice", None, 409, "SUBMITTED", 1),
    ("SUBMITTED:finance_early_approve_refused", "SUBMITTED", "approve", "fiona", {"comment": "Too early"}, 403, "SUBMITTED", 1),
    ("MANAGER_APPROVED:manager_second_approve_refused", "MANAGER_APPROVED", "approve", "bob", {"comment": "Second"}, 403, "MANAGER_APPROVED", 2),
    ("MANAGER_APPROVED:submit_refused", "MANAGER_APPROVED", "submit", "alice", None, 409, "MANAGER_APPROVED", 2),
    ("MANAGER_APPROVED:update_refused", "MANAGER_APPROVED", "update", "alice", None, 409, "MANAGER_APPROVED", 2),
    ("FINANCE_APPROVED:re_approve_refused", "FINANCE_APPROVED", "approve", "fiona", {"comment": "Again"}, 409, "FINANCE_APPROVED", 3),
    ("FINANCE_APPROVED:reject_refused", "FINANCE_APPROVED", "reject", "fiona", {"comment": "Cannot reject"}, 409, "FINANCE_APPROVED", 3),
    ("FINANCE_APPROVED:submit_refused", "FINANCE_APPROVED", "submit", "alice", None, 409, "FINANCE_APPROVED", 3),
    ("REJECTED:approve_refused", "REJECTED", "approve", "bob", {"comment": "Cannot approve"}, 409, "REJECTED", 2),
    ("REJECTED:re_reject_refused", "REJECTED", "reject", "bob", {"comment": "Already rejected"}, 409, "REJECTED", 2),
    ("REJECTED:submit_refused", "REJECTED", "submit", "alice", None, 409, "REJECTED", 2),
]


@pytest.mark.parametrize(
    "case_id,initial_state,action,actor_key,payload,expected_status,target_status,expected_trail_count,expected_last_action",
    ALLOWED_STATE_TRANSITIONS,
    ids=[c[0] for c in ALLOWED_STATE_TRANSITIONS],
)
def test_allowed_state_transitions(
    tokens: dict[str, str],
    case_id: str,
    initial_state: str,
    action: str,
    actor_key: str,
    payload: dict[str, Any] | None,
    expected_status: int,
    target_status: str,
    expected_trail_count: int,
    expected_last_action: str,
) -> None:
    """BR3: Verify every valid state transition succeeds and updates status + approval trail accurately."""
    req_id, initial_trail_count = setup_request_in_state(tokens, initial_state)
    resp = dispatch_action(tokens, req_id, action, actor_key, payload)
    assert resp.status_code == expected_status, f"{case_id} failed: {resp.status_code} {resp.text}"

    # Read back as owner and verify postconditions (status and trail rows)
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["alice"]), timeout=10)
    assert rb.status_code == 200
    data = rb.json()
    assert data["status"] == target_status, f"{case_id}: expected status {target_status}, got {data['status']}"
    assert len(data["approvals"]) == expected_trail_count, f"{case_id}: expected {expected_trail_count} trail rows, got {len(data['approvals'])}"
    assert data["approvals"][-1]["action"] == expected_last_action


@pytest.mark.parametrize(
    "case_id,initial_state,action,actor_key,payload,expected_status,expected_state,expected_trail_count",
    DISALLOWED_STATE_TRANSITIONS,
    ids=[c[0] for c in DISALLOWED_STATE_TRANSITIONS],
)
def test_disallowed_state_transitions(
    tokens: dict[str, str],
    case_id: str,
    initial_state: str,
    action: str,
    actor_key: str,
    payload: dict[str, Any] | None,
    expected_status: int,
    expected_state: str,
    expected_trail_count: int,
) -> None:
    """BR3: Refuse invalid transitions from every state; assert state and approval trail remain unchanged."""
    req_id, initial_trail_count = setup_request_in_state(tokens, initial_state)
    resp = dispatch_action(tokens, req_id, action, actor_key, payload)
    assert resp.status_code == expected_status, f"{case_id}: expected HTTP {expected_status}, got {resp.status_code}: {resp.text}"

    # Read back as owner and verify state and trail rows are unchanged after rejection
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers=auth_headers(tokens["alice"]), timeout=10)
    assert rb.status_code == 200
    data = rb.json()
    assert data["status"] == expected_state, f"{case_id}: status was modified to {data['status']}"
    assert len(data["approvals"]) == expected_trail_count, f"{case_id}: approval trail rows changed from {expected_trail_count} to {len(data['approvals'])}"


def test_double_submit_adds_one_trail_row(tokens: dict[str, str]) -> None:
    """Submit → assert 1 trail row; submit again → assert still 1 trail row (409)."""
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)

    # Read back: exactly 1 approval row (the SUBMIT action)
    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 1, f"Expected 1 trail row after first submit, got {len(rb['approvals'])}"
    assert rb["status"] == "SUBMITTED"

    # Repeat submit must be rejected
    r2 = requests.post(f"{BASE_URL}/api/requests/{d}/submit", headers=auth_headers(tokens["alice"]), timeout=10)
    assert r2.status_code == 409, f"Expected 409 on double-submit, got {r2.status_code}"

    # Trail must still have exactly 1 row — no extra row appended
    rb2 = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb2["approvals"]) == 1, f"Expected still 1 trail row after double-submit, got {len(rb2['approvals'])}"
    assert rb2["status"] == "SUBMITTED", "Status must not change after rejected re-submit"


def test_double_manager_approve_second_returns_403(tokens: dict[str, str]) -> None:
    """Manager approve (200) → 2 trail rows; re-approve by same manager (403) → still 2 rows.

    Why 403 not 409: after the first manager approval the request moves to MANAGER_APPROVED,
    which is owned by the FINANCE stage. A manager calling /approve again is hitting the wrong
    role for that stage, so the server rejects it as Forbidden before even checking idempotency.
    """
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)

    r1 = requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10)
    assert r1.status_code == 200, f"First manager approve must be 200, got {r1.status_code}"

    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 2, f"Expected 2 trail rows (SUBMIT + APPROVE), got {len(rb['approvals'])}"
    assert rb["status"] == "MANAGER_APPROVED"

    # Manager tries to approve again — wrong role for FINANCE stage → 403
    r2 = requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10)
    assert r2.status_code == 403, f"Expected 403 on manager re-approve (wrong stage), got {r2.status_code}"

    # Trail must still have exactly 2 rows
    rb2 = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb2["approvals"]) == 2, f"Expected still 2 trail rows after rejected re-approve, got {len(rb2['approvals'])}"
    assert rb2["status"] == "MANAGER_APPROVED", "Status must not change after rejected re-approve"


def test_double_finance_approve_second_returns_409(tokens: dict[str, str]) -> None:
    """Finance approve (200) → 3 trail rows; re-approve by finance (409) → still 3 rows."""
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)
    requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10)

    r1 = requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["fiona"]), timeout=10)
    assert r1.status_code == 200, f"First finance approve must be 200, got {r1.status_code}"

    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 3, f"Expected 3 trail rows (SUBMIT + MGR_APPROVE + FIN_APPROVE), got {len(rb['approvals'])}"
    assert rb["status"] == "FINANCE_APPROVED"

    # Finance tries to approve again — terminal state → 409
    r2 = requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["fiona"]), timeout=10)
    assert r2.status_code == 409, f"Expected 409 on finance re-approve (terminal state), got {r2.status_code}"

    # Trail must still have exactly 3 rows
    rb2 = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb2["approvals"]) == 3, f"Expected still 3 trail rows after rejected re-approve, got {len(rb2['approvals'])}"
    assert rb2["status"] == "FINANCE_APPROVED", "Status must not change after rejected re-approve"


def test_double_reject_second_returns_409(tokens: dict[str, str]) -> None:
    """Reject (200) → 2 trail rows; re-reject (409) → still 2 rows."""
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)

    r1 = requests.post(f"{BASE_URL}/api/requests/{d}/reject", headers=auth_headers(tokens["bob"]), timeout=10)
    assert r1.status_code == 200, f"First reject must be 200, got {r1.status_code}"

    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 2, f"Expected 2 trail rows (SUBMIT + REJECT), got {len(rb['approvals'])}"
    assert rb["status"] == "REJECTED"

    # Reject again — terminal state → 409
    r2 = requests.post(f"{BASE_URL}/api/requests/{d}/reject", headers=auth_headers(tokens["bob"]), timeout=10)
    assert r2.status_code == 409, f"Expected 409 on re-reject (terminal state), got {r2.status_code}"

    # Trail must still have exactly 2 rows
    rb2 = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb2["approvals"]) == 2, f"Expected still 2 trail rows after rejected re-reject, got {len(rb2['approvals'])}"
    assert rb2["status"] == "REJECTED", "Status must not change after rejected re-reject"


def test_concurrent_double_approve_no_duplicate_trail(tokens: dict[str, str]) -> None:
    """Two threads both call POST /approve simultaneously on a SUBMITTED request.

    Expected: exactly one thread gets 200, the other gets 409 (optimistic-lock conflict) or 403.
    Final trail must have exactly 2 rows (SUBMIT + one APPROVE).
    """
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)

    results: list[int] = []
    barrier = threading.Barrier(2)  # both threads start the POST at the same instant

    def do_approve() -> None:
        barrier.wait()
        r = requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10)
        results.append(r.status_code)

    t1 = threading.Thread(target=do_approve)
    t2 = threading.Thread(target=do_approve)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one success and one conflict/forbidden
    assert sorted(results) in ([200, 403], [200, 409]), (
        f"Expected one 200 and one 403/409 from concurrent approve, got {sorted(results)}"
    )

    # Trail must have exactly 2 rows regardless of race outcome
    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 2, (
        f"Expected exactly 2 trail rows after concurrent approve, got {len(rb['approvals'])}"
    )


def test_unauthenticated_requests_rejected() -> None:
    """Requests without JWT must return 401."""
    resp = requests.get(f"{BASE_URL}/api/requests", timeout=10)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 7. Coverage-gap tests (discovered by the conftest.py API coverage report)
# ---------------------------------------------------------------------------


def test_get_me_returns_current_user_profile(tokens: dict[str, str]) -> None:
    """GET /api/auth/me returns the authenticated user's profile (200).

    This endpoint was flagged as uncovered by the API coverage report.
    """
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers(tokens["alice"]), timeout=10)
    assert resp.status_code == 200, f"Expected 200 from GET /api/auth/me, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["email"] == "alice@acme.com", f"Unexpected email: {body.get('email')}"
    assert body["role"] == "EMPLOYEE", f"Unexpected role: {body.get('role')}"


def test_get_me_unauthenticated_returns_401() -> None:
    """GET /api/auth/me without a token must return 401."""
    resp = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


def test_register_new_employee_returns_201_with_token() -> None:
    """POST /api/auth/register creates a new EMPLOYEE account and returns 201 + JWT.

    This endpoint was flagged as uncovered by the API coverage report.
    Uses a unique email derived from the current timestamp to avoid 409 on reruns.
    """
    import time
    unique_email = f"coverage.gap.{int(time.time())}@acme.com"
    payload = {
        "email": unique_email,
        "password": "Register123",
        "fullName": "Coverage Gap User",
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=10)
    assert resp.status_code == 201, f"Expected 201 from POST /api/auth/register, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "token" in body, f"Response missing 'token': {body}"
    assert body.get("user", {}).get("role") == "EMPLOYEE", f"Expected role EMPLOYEE: {body}"


def test_register_duplicate_email_returns_409() -> None:
    """POST /api/auth/register with an already-registered email must return 409."""
    # alice@acme.com is seeded — trying to register it again must conflict
    payload = {
        "email": "alice@acme.com",
        "password": "AnotherPass1",
        "fullName": "Duplicate Alice",
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=10)
    assert resp.status_code == 409, f"Expected 409 for duplicate email, got {resp.status_code}: {resp.text}"
