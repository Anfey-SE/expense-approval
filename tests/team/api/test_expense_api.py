"""
API & Integration Test Suite (Member 2 — 24i-3097).

Covers:
1. Generated EP & 3-point BVA tests from OpenAPI spec (one invalid value per test).
2. Business rules BR1-BR4 rejections and boundary enforcement.
3. State transition matrix (every allowed transition + disallowed transitions from every state).
4. Repeated requests (double submit/approve/reject -> no duplicate approval trail rows).
5. Cross-workflow read-back assertions after both success and rejection.
6. Endpoint behavior / weakness verification (pagination clamping, blank rejection comment, unauthenticated access).
"""

from __future__ import annotations

import json
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


def test_disallowed_state_transitions_from_every_state(tokens: dict[str, str]) -> None:
    """BR3: Test disallowed transitions from DRAFT, SUBMITTED, MANAGER_APPROVED, FINANCE_APPROVED, REJECTED."""
    # 1. From DRAFT: cannot approve or reject
    d1 = create_draft(tokens["alice"])["id"]
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 409
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/reject", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 409
    # Non-owner cannot submit
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/submit", headers=auth_headers(tokens["carol"]), timeout=10).status_code == 403

    # 2. From SUBMITTED: cannot update or re-submit
    submit_request(tokens["alice"], d1)
    assert requests.put(
        f"{BASE_URL}/api/requests/{d1}",
        headers=auth_headers(tokens["alice"]),
        json=valid_request_payload(),
        timeout=10,
    ).status_code == 409
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/submit", headers=auth_headers(tokens["alice"]), timeout=10).status_code == 409

    # 3. From MANAGER_APPROVED: manager approves to enter state (200), then cannot approve again (403), owner cannot submit (409)
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 403
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/submit", headers=auth_headers(tokens["alice"]), timeout=10).status_code == 409

    # 4. From FINANCE_APPROVED: terminal state — no further approve/reject/submit
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/approve", headers=auth_headers(tokens["fiona"]), timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/approve", headers=auth_headers(tokens["fiona"]), timeout=10).status_code == 409
    assert requests.post(f"{BASE_URL}/api/requests/{d1}/reject", headers=auth_headers(tokens["fiona"]), timeout=10).status_code == 409

    # 5. From REJECTED: terminal state — no further approve/reject/submit
    d2 = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d2)
    assert requests.post(f"{BASE_URL}/api/requests/{d2}/reject", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/api/requests/{d2}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 409
    assert requests.post(f"{BASE_URL}/api/requests/{d2}/reject", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 409
    assert requests.post(f"{BASE_URL}/api/requests/{d2}/submit", headers=auth_headers(tokens["alice"]), timeout=10).status_code == 409


def test_repeated_requests_no_duplicate_trail_rows(tokens: dict[str, str]) -> None:
    """Repeated submit, approve, and reject requests must fail and never append duplicate approval trail rows."""
    d = create_draft(tokens["alice"])["id"]
    submit_request(tokens["alice"], d)
    # Repeat submit -> 409
    assert requests.post(f"{BASE_URL}/api/requests/{d}/submit", headers=auth_headers(tokens["alice"]), timeout=10).status_code == 409

    # Manager approve -> 200, repeat -> 403 (stage is now FINANCE)
    assert requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["bob"]), timeout=10).status_code == 403

    # Finance approve -> 200, repeat -> 409
    assert requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["fiona"]), timeout=10).status_code == 200
    assert requests.post(f"{BASE_URL}/api/requests/{d}/approve", headers=auth_headers(tokens["fiona"]), timeout=10).status_code == 409

    rb = requests.get(f"{BASE_URL}/api/requests/{d}", headers=auth_headers(tokens["alice"]), timeout=10).json()
    assert len(rb["approvals"]) == 3, f"Expected exactly 3 trail rows, got {len(rb['approvals'])}"


def test_unauthenticated_requests_rejected() -> None:
    """Requests without JWT must return 401."""
    resp = requests.get(f"{BASE_URL}/api/requests", timeout=10)
    assert resp.status_code == 401
