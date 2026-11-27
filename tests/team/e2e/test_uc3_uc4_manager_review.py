"""
Playwright E2E Tests for Member 2 Use Cases: UC3 & UC4 (Manager Review).

UC3: Manager approves a submitted request (Main Flow, 2 Alternative Flows, 2 Exception Flows)
UC4: Manager rejects a submitted request (Main Flow, 2 Alternative Flows, 2 Exception Flows)

Every flow asserts both the displayed UI result and the persisted postcondition
(via page reload and/or API read-back).
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

import pytest
import requests
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("EXPENSE_BASE_URL", "http://localhost:8081").rstrip("/")


def api_login(email: str, password: str = "password123") -> str:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=10)
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["token"]


def api_create_and_submit(email: str, title: str, amount: float = 42.50) -> dict[str, Any]:
    token = api_login(email)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "description": "E2E test expense",
        "currency": "USD",
        "items": [
            {
                "description": "Client dinner",
                "category": "Meals",
                "amount": amount,
                "incurredOn": (dt.date.today() - dt.timedelta(days=1)).isoformat(),
            }
        ],
    }
    c = requests.post(f"{BASE_URL}/api/requests", headers=headers, json=payload, timeout=10)
    assert c.status_code == 201
    req_id = c.json()["id"]
    s = requests.post(f"{BASE_URL}/api/requests/{req_id}/submit", headers=headers, timeout=10)
    assert s.status_code == 200
    return s.json()


def ui_login(page: Page, email: str, password: str = "password123") -> None:
    page.goto(f"{BASE_URL}/login")
    page.locator('input[type="email"]').fill(email)
    page.locator('input[type="password"]').fill(password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("button", name="Log out")).to_be_visible(timeout=10000)


# ===========================================================================
# UC3: Manager Approves a Submitted Request
# ===========================================================================


def test_uc3_main_and_alt1_approve_with_comment(page: Page) -> None:
    """UC3-MF & UC3-AF1: Manager approves a submitted request with a comment and verifies postcondition."""
    req = api_create_and_submit("alice@acme.com", "UC3 Travel Expense")
    req_id = req["id"]

    ui_login(page, "bob@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    expect(page.get_by_role("heading", name="UC3 Travel Expense")).to_be_visible()

    # Enter approval comment (UC3-AF1) and click Approve
    page.locator("input[maxlength='500']").fill("Approved within Q4 travel budget")
    page.get_by_role("button", name="Approve").click()

    # Assert displayed UI result
    expect(page.locator("text=manager approved").first).to_be_visible(timeout=10000)
    expect(page.get_by_text("Approved within Q4 travel budget")).to_be_visible()
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)

    # Assert postcondition after reload and via API read-back
    page.reload()
    expect(page.locator("text=manager approved").first).to_be_visible()
    bob_token = api_login("bob@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb["status"] == "MANAGER_APPROVED"
    assert rb["approvals"][-1]["action"] == "APPROVE"
    assert rb["approvals"][-1]["comment"] == "Approved within Q4 travel budget"


def test_uc3_alt2_approve_from_inbox_among_multiple(page: Page) -> None:
    """UC3-AF2: Manager approves one of several pending requests directly from the approval inbox."""
    req1 = api_create_and_submit("alice@acme.com", "UC3 Inbox Target")
    req2 = api_create_and_submit("alice@acme.com", "UC3 Inbox Sibling")

    ui_login(page, "bob@acme.com")
    expect(page.get_by_text("Awaiting your approval", exact=True)).to_be_visible()

    # Locate the inbox row for req1 and click Approve
    inbox_row = page.locator("tr", has_text="UC3 Inbox Target").first
    expect(inbox_row).to_be_visible()
    inbox_row.get_by_role("button", name="Approve").click()

    # Verify req1 leaves the inbox while req2 remains
    expect(page.locator("tr", has_text="UC3 Inbox Sibling").first).to_be_visible()
    bob_token = api_login("bob@acme.com")
    rb1 = requests.get(f"{BASE_URL}/api/requests/{req1['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    rb2 = requests.get(f"{BASE_URL}/api/requests/{req2['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb1["status"] == "MANAGER_APPROVED"
    assert rb2["status"] == "SUBMITTED"


def test_uc3_exc1_cross_department_manager_denied(page: Page) -> None:
    """UC3-EF1: Manager from a different department (Sales) cannot view or approve Engineering request."""
    req = api_create_and_submit("alice@acme.com", "UC3 Cross Dept Check")

    ui_login(page, "dave@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.locator(".error")).to_contain_text("Request not found")

    # Postcondition: request remains SUBMITTED
    alice_token = api_login("alice@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {alice_token}"}, timeout=10).json()
    assert rb["status"] == "SUBMITTED"


def test_uc3_exc2_not_submitted_and_self_approval_blocked(page: Page) -> None:
    """UC3-EF2: Manager cannot approve a DRAFT request or their own SUBMITTED request."""
    # Own submitted request
    own_req = api_create_and_submit("bob@acme.com", "UC3 Bob Own Expense")
    ui_login(page, "bob@acme.com")
    page.goto(f"{BASE_URL}/requests/{own_req['id']}")
    expect(page.get_by_role("heading", name="UC3 Bob Own Expense")).to_be_visible()
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)

    # Postcondition: own request remains SUBMITTED
    bob_token = api_login("bob@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{own_req['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb["status"] == "SUBMITTED"


# ===========================================================================
# UC4: Manager Rejects a Submitted Request
# ===========================================================================


def test_uc4_main_and_alt2_reject_and_employee_views_outcome(page: Page) -> None:
    """UC4-MF & UC4-AF2: Manager rejects with reason; Employee views the rejected outcome and trail."""
    req = api_create_and_submit("alice@acme.com", "UC4 Missing Receipt")
    req_id = req["id"]

    ui_login(page, "bob@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    page.locator("input[maxlength='500']").fill("Receipt missing for meal")
    page.get_by_role("button", name="Reject").click()

    expect(page.locator("text=rejected").first).to_be_visible(timeout=10000)
    expect(page.get_by_text("Receipt missing for meal")).to_be_visible()

    # Sign out and sign in as Employee (UC4-AF2)
    page.get_by_role("button", name="Log out").click()
    ui_login(page, "alice@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    expect(page.locator("text=rejected").first).to_be_visible()
    expect(page.get_by_text("Receipt missing for meal")).to_be_visible()

    # Postcondition via API
    alice_token = api_login("alice@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers={"Authorization": f"Bearer {alice_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert len(rb["approvals"]) == 2
    assert rb["approvals"][1]["action"] == "REJECT"


def test_uc4_alt1_reject_from_inbox_with_prompt(page: Page) -> None:
    """UC4-AF1: Manager rejects directly from inbox via browser prompt dialog."""
    req = api_create_and_submit("alice@acme.com", "UC4 Inbox Reject")

    ui_login(page, "bob@acme.com")
    page.on("dialog", lambda dialog: dialog.accept("Over meal cap"))
    inbox_row = page.locator("tr", has_text="UC4 Inbox Reject").first
    expect(inbox_row).to_be_visible()
    inbox_row.get_by_role("button", name="Reject").click()

    page.wait_for_timeout(500)
    bob_token = api_login("bob@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert rb["approvals"][-1]["comment"] == "Over meal cap"


def test_uc4_exc1_reject_without_reason_allowed(page: Page) -> None:
    """UC4-EF1: Manager clicks Reject without entering a reason; app allows blank comment (EW-2)."""
    req = api_create_and_submit("alice@acme.com", "UC4 Blank Reason")

    ui_login(page, "bob@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    page.get_by_role("button", name="Reject").click()

    expect(page.locator("text=rejected").first).to_be_visible(timeout=10000)
    bob_token = api_login("bob@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert rb["approvals"][-1]["comment"] == ""


def test_uc4_exc2_cannot_reject_already_approved_request(page: Page) -> None:
    """UC4-EF2: Manager cannot reject a request that is already MANAGER_APPROVED."""
    req = api_create_and_submit("alice@acme.com", "UC4 Already Approved")
    bob_token = api_login("bob@acme.com")
    requests.post(
        f"{BASE_URL}/api/requests/{req['id']}/approve",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"comment": "First approval"},
        timeout=10,
    )

    ui_login(page, "bob@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.locator("text=manager approved").first).to_be_visible()
    expect(page.get_by_role("button", name="Reject")).to_have_count(0)

    # Postcondition: status remains MANAGER_APPROVED, trail count remains 2
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {bob_token}"}, timeout=10).json()
    assert rb["status"] == "MANAGER_APPROVED"
    assert len(rb["approvals"]) == 2
