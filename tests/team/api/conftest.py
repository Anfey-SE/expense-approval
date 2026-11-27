"""Pytest fixtures and helpers for Member 2 API & Integration tests."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import requests as _requests
import yaml

BASE_URL = os.environ.get("EXPENSE_BASE_URL", "http://localhost:8081").rstrip("/")
DATA_FILE = Path(__file__).resolve().parent / "generated_test_data.json"
OPENAPI_FILE = Path(__file__).resolve().parent / "openapi.yaml"
COVERAGE_REPORT = Path(__file__).resolve().parent.parent.parent / "docs" / "team" / "evidence" / "api_coverage_report.txt"

USERS = {
    "alice": ("alice@acme.com", "password123"),   # EMPLOYEE, Engineering
    "bob": ("bob@acme.com", "password123"),       # MANAGER, Engineering
    "carol": ("carol@acme.com", "password123"),   # EMPLOYEE, Sales
    "dave": ("dave@acme.com", "password123"),     # MANAGER, Sales
    "fiona": ("fiona@acme.com", "password123"),   # FINANCE, Finance
}

# ---------------------------------------------------------------------------
# API coverage tracking
# Collects every (METHOD, normalised_path, status_code) the test suite hits.
# "Normalised path" replaces all numeric path segments with {id}.
# ---------------------------------------------------------------------------
_observed: dict[tuple[str, str], set[int]] = defaultdict(set)
_observed_params: dict[tuple[str, str], set[str]] = defaultdict(set)

_original_request = _requests.Session.request


def _tracking_request(self: _requests.Session, method: str, url: str, **kwargs: Any) -> _requests.Response:
    """Wrapper around requests.Session.request that records (method, path, status_code)."""
    resp = _original_request(self, method, url, **kwargs)
    # Normalise: strip base URL, replace numeric segments with {id}
    path = url
    if path.startswith(BASE_URL):
        path = path[len(BASE_URL):]
    path = re.sub(r"/\d+", "/{id}", path)
    # Remove query string from path key
    path = path.split("?")[0]
    key = (method.upper(), path)
    _observed[key].add(resp.status_code)
    # Track query params used
    params = kwargs.get("params") or {}
    for p in params:
        _observed_params[key].add(str(p))
    return resp


_requests.Session.request = _tracking_request  # type: ignore[method-assign]


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
        resp = _requests.post(
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
    resp = _requests.post(
        f"{BASE_URL}/api/requests",
        headers=auth_headers(token),
        json=payload or valid_request_payload(),
        timeout=10,
    )
    assert resp.status_code == 201, f"Expected 201 creating draft, got {resp.status_code}: {resp.text}"
    return resp.json()


def submit_request(token: str, req_id: int) -> dict[str, Any]:
    resp = _requests.post(
        f"{BASE_URL}/api/requests/{req_id}/submit",
        headers=auth_headers(token),
        timeout=10,
    )
    assert resp.status_code == 200, f"Expected 200 submitting {req_id}, got {resp.status_code}: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# API coverage report (runs at end of session)
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    """Compare observed (method, path, status_code) against openapi.yaml and write a coverage report."""
    if not OPENAPI_FILE.exists():
        return

    spec = yaml.safe_load(OPENAPI_FILE.read_text(encoding="utf-8"))
    paths_spec = spec.get("paths", {})

    # Build the spec inventory: {(METHOD, normalised_path): {status_codes}, params}
    spec_endpoints: dict[tuple[str, str], set[int]] = {}
    spec_params: dict[tuple[str, str], set[str]] = {}

    for raw_path, path_item in paths_spec.items():
        norm_path = re.sub(r"\{[^}]+\}", "{id}", raw_path)

        path_params = {p["name"] for p in path_item.get("parameters", []) if p.get("in") == "query"}

        for method in ("get", "post", "put", "delete", "patch"):
            if method not in path_item:
                continue
            op = path_item[method]
            status_codes = {int(sc) for sc in op.get("responses", {}).keys()}
            query_params = path_params | {
                p["name"] for p in op.get("parameters", []) if p.get("in") == "query"
            }
            key = (method.upper(), norm_path)
            spec_endpoints[key] = status_codes
            spec_params[key] = query_params

    total_endpoints = len(spec_endpoints)
    hit_endpoints = sum(1 for k in spec_endpoints if k in _observed)
    total_status_codes = sum(len(v) for v in spec_endpoints.values())
    hit_status_codes = sum(
        len(spec_endpoints[k] & _observed.get(k, set()))
        for k in spec_endpoints
    )
    total_params = sum(len(v) for v in spec_params.values())
    hit_params = sum(
        len(spec_params[k] & _observed_params.get(k, set()))
        for k in spec_params
    )

    lines: list[str] = [
        "=" * 70,
        "API COVERAGE REPORT — Member 2 (24i-3097)",
        "=" * 70,
        "",
        f"Endpoint coverage : {hit_endpoints}/{total_endpoints} = {hit_endpoints/max(total_endpoints,1)*100:.1f}%",
        f"Status-code coverage : {hit_status_codes}/{total_status_codes} = {hit_status_codes/max(total_status_codes,1)*100:.1f}%",
        f"Query-param coverage : {hit_params}/{total_params} = {hit_params/max(total_params,1)*100:.1f}%",
        "",
        "-" * 70,
        "UNCOVERED ENDPOINTS (not hit at all):",
    ]
    for key in sorted(spec_endpoints):
        if key not in _observed:
            lines.append(f"  {key[0]:6} {key[1]}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("UNCOVERED STATUS CODES (endpoint hit but status code never triggered):")
    for key in sorted(spec_endpoints):
        if key not in _observed:
            continue
        missed = spec_endpoints[key] - _observed.get(key, set())
        if missed:
            lines.append(f"  {key[0]:6} {key[1]}  — missing: {sorted(missed)}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("UNCOVERED QUERY PARAMS (param never passed in a request):")
    for key in sorted(spec_params):
        missed = spec_params[key] - _observed_params.get(key, set())
        if missed:
            lines.append(f"  {key[0]:6} {key[1]}  — missing params: {sorted(missed)}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("OBSERVED BUT NOT IN SPEC (extra paths the tests hit):")
    for key in sorted(_observed):
        if key not in spec_endpoints:
            lines.append(f"  {key[0]:6} {key[1]}  status codes: {sorted(_observed[key])}")
    lines.append("")
    lines.append("=" * 70)

    report_text = "\n".join(lines)
    print("\n" + report_text)

    COVERAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_REPORT.write_text(report_text, encoding="utf-8")
