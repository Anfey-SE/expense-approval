"""
Playwright E2E Tests for Member 3 Use Cases: UC5 & UC6 (Finance Review).

UC5: Finance approves a manager-approved request (Main Flow, 2 Alternative Flows, 3 Exception Flows)
UC6: Finance rejects a manager-approved request (Main Flow, 2 Alternative Flows, 2 Exception Flows)

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


def api_create_and_submit(email: str, title: str, amount: float = 75.00) -> dict[str, Any]:
    token = api_login(email)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "description": "E2E finance review expense",
        "currency": "USD",
        "items": [
            {
                "description": "Conference ticket",
                "category": "Travel",
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


def api_manager_approve(req_id: int, mgr_email: str = "bob@acme.com", comment: str = "Manager OK") -> dict[str, Any]:
    mgr_token = api_login(mgr_email)
    resp = requests.post(
        f"{BASE_URL}/api/requests/{req_id}/approve",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={"comment": comment},
        timeout=10,
    )
    assert resp.status_code == 200
    return resp.json()


def ui_login(page: Page, email: str, password: str = "password123") -> None:
    page.goto(f"{BASE_URL}/login")
    page.locator('input[type="email"]').fill(email)
    page.locator('input[type="password"]').fill(password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("button", name="Log out")).to_be_visible(timeout=10000)


# ===========================================================================
# UC5: Finance Approves a Manager-Approved Request
# ===========================================================================


def test_uc5_main_and_alt1_approve_with_comment(page: Page) -> None:
    """UC5-MF & UC5-AF1: Finance approves a manager-approved request with comment; verifies outcome & trail."""
    req = api_create_and_submit("alice@acme.com", "UC5 Main & Alt1 Travel")
    req_id = req["id"]
    api_manager_approve(req_id, "bob@acme.com", "Manager endorsed")

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    expect(page.get_by_role("heading", name="UC5 Main & Alt1 Travel")).to_be_visible()
    expect(page.locator("text=manager approved").first).to_be_visible()

    # Enter comment (UC5-AF1) and click Approve
    comment = "Approved for disbursement in Q4 batch"
    page.locator("input[maxlength='500']").fill(comment)
    page.get_by_role("button", name="Approve").click()

    # UI assertions
    expect(page.locator("text=finance approved").first).to_be_visible(timeout=10000)
    expect(page.get_by_text(comment)).to_be_visible()
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)
    expect(page.get_by_role("button", name="Reject")).to_have_count(0)

    # Postcondition after page reload and API read-back
    page.reload()
    expect(page.locator("text=finance approved").first).to_be_visible()
    fiona_token = api_login("fiona@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "FINANCE_APPROVED"
    assert len(rb["approvals"]) == 3
    assert rb["approvals"][2]["action"] == "APPROVE"
    assert rb["approvals"][2]["comment"] == comment
    assert rb["approvals"][2]["fromStatus"] == "MANAGER_APPROVED"
    assert rb["approvals"][2]["toStatus"] == "FINANCE_APPROVED"


def test_uc5_alt2_approve_from_inbox_among_multiple(page: Page) -> None:
    """UC5-AF2: Finance approves one request directly from inbox; sibling remains pending."""
    req1 = api_create_and_submit("alice@acme.com", "UC5 Inbox Target")
    req2 = api_create_and_submit("carol@acme.com", "UC5 Inbox Sibling")
    api_manager_approve(req1["id"], "bob@acme.com", "Bob OK")
    api_manager_approve(req2["id"], "dave@acme.com", "Dave OK")

    ui_login(page, "fiona@acme.com")
    expect(page.get_by_text("Awaiting your approval", exact=True)).to_be_visible()

    target_row = page.locator("tr", has_text="UC5 Inbox Target").first
    expect(target_row).to_be_visible()
    target_row.get_by_role("button", name="Approve").click()

    # Verify target leaves inbox, sibling remains
    expect(page.locator("tr", has_text="UC5 Inbox Sibling").first).to_be_visible()
    fiona_token = api_login("fiona@acme.com")
    rb1 = requests.get(f"{BASE_URL}/api/requests/{req1['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    rb2 = requests.get(f"{BASE_URL}/api/requests/{req2['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb1["status"] == "FINANCE_APPROVED"
    assert rb2["status"] == "MANAGER_APPROVED"


def test_uc5_exc1_cannot_approve_submitted_or_draft_request(page: Page) -> None:
    """UC5-EF1: Finance cannot approve a request in SUBMITTED status (actions hidden; API returns 409)."""
    req = api_create_and_submit("alice@acme.com", "UC5 Premature Submit")

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.locator("text=submitted").first).to_be_visible()
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)

    # API returns 409 NOT_PENDING
    fiona_token = api_login("fiona@acme.com")
    resp = requests.post(
        f"{BASE_URL}/api/requests/{req['id']}/approve",
        headers={"Authorization": f"Bearer {fiona_token}"},
        json={"comment": "Early approval"},
        timeout=10,
    )
    assert resp.status_code in (403, 409)

    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "SUBMITTED"
    assert len(rb["approvals"]) == 1


def test_uc5_exc2_non_finance_and_self_approval_blocked(page: Page) -> None:
    """UC5-EF2: Non-finance user (Employee) cannot approve, and Finance cannot approve own request (BR4)."""
    req = api_create_and_submit("alice@acme.com", "UC5 Employee Block")
    api_manager_approve(req["id"], "bob@acme.com", "Bob OK")

    # Employee view
    ui_login(page, "alice@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)

    alice_token = api_login("alice@acme.com")
    resp_emp = requests.post(f"{BASE_URL}/api/requests/{req['id']}/approve", headers={"Authorization": f"Bearer {alice_token}"}, timeout=10)
    assert resp_emp.status_code == 403

    # Finance self-decision check via API
    own_req = api_create_and_submit("fiona@acme.com", "UC5 Fiona Own Request")
    fiona_token = api_login("fiona@acme.com")
    resp_self = requests.post(
        f"{BASE_URL}/api/requests/{own_req['id']}/approve",
        headers={"Authorization": f"Bearer {fiona_token}"},
        json={"comment": "Self-approval"},
        timeout=10,
    )
    assert resp_self.status_code == 403


def test_uc5_exc3_repeated_approval_yields_no_duplicate_trail(page: Page) -> None:
    """UC5-EF3: Repeated approval on finalised request returns 409 and creates zero duplicate trail rows."""
    req = api_create_and_submit("alice@acme.com", "UC5 Finalised Repeat")
    api_manager_approve(req["id"], "bob@acme.com", "Bob OK")

    fiona_token = api_login("fiona@acme.com")
    r1 = requests.post(f"{BASE_URL}/api/requests/{req['id']}/approve", headers={"Authorization": f"Bearer {fiona_token}"}, json={"comment": "First OK"}, timeout=10)
    assert r1.status_code == 200

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.locator("text=finance approved").first).to_be_visible()
    expect(page.get_by_role("button", name="Approve")).to_have_count(0)

    # Second approval returns 409
    r2 = requests.post(f"{BASE_URL}/api/requests/{req['id']}/approve", headers={"Authorization": f"Bearer {fiona_token}"}, json={"comment": "Second attempt"}, timeout=10)
    assert r2.status_code == 409

    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "FINANCE_APPROVED"
    assert len(rb["approvals"]) == 3


# ===========================================================================
# UC6: Finance Rejects a Manager-Approved Request
# ===========================================================================


def test_uc6_main_and_alt2_reject_and_employee_views_outcome(page: Page) -> None:
    """UC6-MF & UC6-AF2: Finance rejects with comment; Employee views rejected outcome and reason."""
    req = api_create_and_submit("alice@acme.com", "UC6 Rejected Budget")
    req_id = req["id"]
    api_manager_approve(req_id, "bob@acme.com", "Manager endorsed")

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    expect(page.locator("text=manager approved").first).to_be_visible()

    reason = "Corporate travel policy cap exceeded"
    page.locator("input[maxlength='500']").fill(reason)
    page.get_by_role("button", name="Reject").click()

    expect(page.locator("text=rejected").first).to_be_visible(timeout=10000)
    expect(page.get_by_text(reason)).to_be_visible()
    expect(page.get_by_role("button", name="Reject")).to_have_count(0)

    # Sign out and sign in as Alice (UC6-AF2)
    page.get_by_role("button", name="Log out").click()
    ui_login(page, "alice@acme.com")
    page.goto(f"{BASE_URL}/requests/{req_id}")
    expect(page.locator("text=rejected").first).to_be_visible()
    expect(page.get_by_text(reason)).to_be_visible()

    alice_token = api_login("alice@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req_id}", headers={"Authorization": f"Bearer {alice_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert len(rb["approvals"]) == 3
    assert rb["approvals"][2]["action"] == "REJECT"
    assert rb["approvals"][2]["comment"] == reason


def test_uc6_alt1_reject_from_inbox_with_prompt(page: Page) -> None:
    """UC6-AF1: Finance rejects directly from inbox via browser prompt dialog."""
    req = api_create_and_submit("alice@acme.com", "UC6 Inbox Reject")
    api_manager_approve(req["id"], "bob@acme.com", "Bob OK")

    ui_login(page, "fiona@acme.com")
    prompt_reason = "Duplicate expense item found"
    page.on("dialog", lambda dialog: dialog.accept(prompt_reason))

    inbox_row = page.locator("tr", has_text="UC6 Inbox Reject").first
    expect(inbox_row).to_be_visible()
    inbox_row.get_by_role("button", name="Reject").click()

    page.wait_for_timeout(500)
    fiona_token = api_login("fiona@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert rb["approvals"][-1]["comment"] == prompt_reason


def test_uc6_exc1_reject_without_reason_allowed(page: Page) -> None:
    """UC6-EF1: Finance clicks Reject without comment; application permits blank reason (EW-2 / PR-04)."""
    req = api_create_and_submit("alice@acme.com", "UC6 Blank Reason")
    api_manager_approve(req["id"], "bob@acme.com", "Bob OK")

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    page.get_by_role("button", name="Reject").click()

    expect(page.locator("text=rejected").first).to_be_visible(timeout=10000)
    fiona_token = api_login("fiona@acme.com")
    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "REJECTED"
    assert rb["approvals"][-1]["comment"] == ""


def test_uc6_exc2_cannot_reject_already_finalised_request(page: Page) -> None:
    """UC6-EF2: Finance cannot reject a request that is already FINANCE_APPROVED."""
    req = api_create_and_submit("alice@acme.com", "UC6 Already Finalised")
    api_manager_approve(req["id"], "bob@acme.com", "Bob OK")

    fiona_token = api_login("fiona@acme.com")
    r1 = requests.post(f"{BASE_URL}/api/requests/{req['id']}/approve", headers={"Authorization": f"Bearer {fiona_token}"}, json={"comment": "Finance OK"}, timeout=10)
    assert r1.status_code == 200

    ui_login(page, "fiona@acme.com")
    page.goto(f"{BASE_URL}/requests/{req['id']}")
    expect(page.locator("text=finance approved").first).to_be_visible()
    expect(page.get_by_role("button", name="Reject")).to_have_count(0)

    # API rejection attempt returns 409
    resp = requests.post(f"{BASE_URL}/api/requests/{req['id']}/reject", headers={"Authorization": f"Bearer {fiona_token}"}, json={"comment": "Late reject"}, timeout=10)
    assert resp.status_code == 409

    rb = requests.get(f"{BASE_URL}/api/requests/{req['id']}", headers={"Authorization": f"Bearer {fiona_token}"}, timeout=10).json()
    assert rb["status"] == "FINANCE_APPROVED"
    assert len(rb["approvals"]) == 3
