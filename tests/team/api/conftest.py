"""Pytest fixtures and helpers for Member 2 API & Integration tests."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import pytest
import requests

BASE_URL = os.environ.get("EXPENSE_BASE_URL", "http://localhost:8081").rstrip("/")
DATA_FILE = Path(__file__).resolve().parent / "generated_test_data.json"

USERS = {
    "alice": ("alice@acme.com", "password123"),   # EMPLOYEE, Engineering
    "bob": ("bob@acme.com", "password123"),       # MANAGER, Engineering
    "carol": ("carol@acme.com", "password123"),   # EMPLOYEE, Sales
    "dave": ("dave@acme.com", "password123"),     # MANAGER, Sales
    "fiona": ("fiona@acme.com", "password123"),   # FINANCE, Finance
}


@pytest.fixture(scope="session")
def generated_data() -> dict[str, Any]:
    """Load the EP and 3-point BVA dataset generated from openapi.yaml."""
    assert DATA_FILE.exists(), f"Run generate_test_data.py first: missing {DATA_FILE}"
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def tokens() -> dict[str, str]:
    """Authenticate each seeded user once per test session."""
    result: dict[str, str] = {}
    for name, (email, password) in USERS.items():
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        assert resp.status_code == 200, f"Login failed for {email}: {resp.status_code} {resp.text}"
        result[name] = resp.json()["token"]
    return result


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def valid_item(**overrides: Any) -> dict[str, Any]:
    item = {
        "description": "Team lunch",
        "category": "Meals",
        "amount": 25.50,
        "incurredOn": (dt.date.today() - dt.timedelta(days=1)).isoformat(),
    }
    item.update(overrides)
    return item


def valid_request_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Q4 Client Travel",
        "description": "Flight and meals",
        "currency": "USD",
        "items": [valid_item()],
    }
    payload.update(overrides)
    return payload


def create_draft(token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = requests.post(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(token),
        json=payload or valid_request_payload(),
        timeout=10,
    )
    assert resp.status_code == 201, f"Expected 201 creating draft, got {resp.status_code}: {resp.text}"
    return resp.json()


def submit_request(token: str, req_id: int) -> dict[str, Any]:
    resp = requests.post(
        f"{BASE_URL}/api/requests/{req_id}/submit",
        headers=auth_headers(token),
        timeout=10,
    )
    assert resp.status_code == 200, f"Expected 200 submitting {req_id}, got {resp.status_code}: {resp.text}"
    return resp.json()
