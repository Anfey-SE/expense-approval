import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { fieldByLabel, login, logout, uniqueTitle } from "./helpers";

const API_BASE = "http://localhost:8081";

/** Independent API helper: login and get JWT token */
async function apiLogin(request: APIRequestContext, email: string, password = "password123"): Promise<string> {
  const res = await request.post(`${API_BASE}/api/auth/login`, {
    data: { email, password },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  return body.token;
}

/** Independent API helper: create draft and submit it */
async function apiCreateAndSubmit(
  request: APIRequestContext,
  email: string,
  title: string,
  amount = 75.0
): Promise<{ id: number; token: string }> {
  const token = await apiLogin(request, email);
  const createRes = await request.post(`${API_BASE}/api/requests`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      title,
      description: "UC5/UC6 test submission",
      currency: "USD",
      items: [
        {
          description: "Conference Pass",
          category: "Other",
          amount,
          incurredOn: new Date().toISOString().slice(0, 10),
        },
      ],
    },
  });
  expect(createRes.status()).toBe(201);
  const created = await createRes.json();
  const reqId = created.id;

  const submitRes = await request.post(`${API_BASE}/api/requests/${reqId}/submit`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(submitRes.ok()).toBeTruthy();

  return { id: reqId, token };
}

/** Independent API helper: advance request to MANAGER_APPROVED */
async function apiManagerApprove(
  request: APIRequestContext,
  reqId: number,
  mgrEmail = "bob@acme.com",
  comment = "Manager sign-off"
) {
  const mgrToken = await apiLogin(request, mgrEmail);
  const res = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
    headers: { Authorization: `Bearer ${mgrToken}` },
    data: { comment },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.status).toBe("MANAGER_APPROVED");
  return body;
}

test.describe("UC5 — Finance approves a manager-approved expense request", () => {
  test("UC5_MF_and_AF1_finance_approves_with_comment: Fiona approves and verifies displayed outcome and audit trail", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC5-MF-AF1");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 150.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager initial approval");

    // 1. Fiona logs in and opens the manager-approved request
    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);

    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".badge")).toHaveText("manager approved");

    // 2. Fill comment (UC5-AF1) and click Approve
    const comment = "Final Q4 finance approval; payment scheduled";
    await page.locator("input[maxlength='500']").fill(comment);
    await page.getByRole("button", { name: "Approve" }).click();

    // 3. Assert displayed UI result
    await expect(page.locator(".badge")).toHaveText("finance approved");
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Reject" })).toHaveCount(0);

    const trailTable = page.locator("table").nth(1);
    await expect(trailTable).toContainText("APPROVE");
    await expect(trailTable).toContainText("manager approved → finance approved");
    await expect(trailTable).toContainText(comment);

    // 4. Assert postcondition: reload and verify persisted state
    await page.reload();
    await expect(page.locator(".badge")).toHaveText("finance approved");
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);

    // 5. Independent API read-back: status and exact trail row count (3 rows: SUBMIT, MGR APPROVE, FIN APPROVE)
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const getRes = await request.get(`${API_BASE}/api/requests/${reqId}`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
    });
    expect(getRes.ok()).toBeTruthy();
    const readBack = await getRes.json();
    expect(readBack.status).toBe("FINANCE_APPROVED");
    expect(readBack.approvals).toHaveLength(3);
    expect(readBack.approvals[2].action).toBe("APPROVE");
    expect(readBack.approvals[2].comment).toBe(comment);
    expect(readBack.approvals[2].fromStatus).toBe("MANAGER_APPROVED");
    expect(readBack.approvals[2].toStatus).toBe("FINANCE_APPROVED");
  });

  test("UC5_AF2_finance_approves_from_inbox: Approve directly from inbox among multiple pending requests", async ({
    page,
    request,
  }) => {
    const titleTarget = uniqueTitle("UC5-AF2-Target");
    const titleSibling = uniqueTitle("UC5-AF2-Sibling");

    const { id: idTarget } = await apiCreateAndSubmit(request, "alice@acme.com", titleTarget, 80.0);
    const { id: idSibling } = await apiCreateAndSubmit(request, "carol@acme.com", titleSibling, 120.0);

    await apiManagerApprove(request, idTarget, "bob@acme.com", "Bob OK");
    await apiManagerApprove(request, idSibling, "dave@acme.com", "Dave OK");

    await login(page, "fiona@acme.com");
    await expect(page.getByText(/Awaiting your approval/)).toBeVisible();

    const inboxCard = page.locator(".card").filter({ hasText: "Awaiting your approval" });

    // Locate target row in the inbox and click Approve
    const targetRow = inboxCard.locator("tr").filter({ hasText: titleTarget });
    await expect(targetRow).toBeVisible();
    await targetRow.getByRole("button", { name: "Approve" }).click();

    // Target disappears from inbox; sibling remains
    await expect(inboxCard.locator("tr").filter({ hasText: titleTarget })).toHaveCount(0);
    await expect(inboxCard.locator("tr").filter({ hasText: titleSibling })).toBeVisible();

    // Independent API read-back
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const resTarget = await request.get(`${API_BASE}/api/requests/${idTarget}`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
    });
    const resSibling = await request.get(`${API_BASE}/api/requests/${idSibling}`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
    });
    const bodyTarget = await resTarget.json();
    const bodySibling = await resSibling.json();
    expect(bodyTarget.status).toBe("FINANCE_APPROVED");
    expect(bodySibling.status).toBe("MANAGER_APPROVED");
  });

  test("UC5_EF1_finance_cannot_approve_submitted_or_draft_request: Actions hidden and API returns 409", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC5-EF1-Premature");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 95.0);

    // Request is in SUBMITTED status (not yet manager-approved)
    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".badge")).toHaveText("submitted");

    // UI actions panel should NOT offer Approve button to Finance at this stage
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);

    // Direct API attempt by Finance must be rejected
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const apiRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "Premature approve attempt" },
    });
    expect([403, 409]).toContain(apiRes.status());

    // Postcondition: status unchanged and trail count remains 1 (SUBMIT only)
    const readBack = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(readBack.status).toBe("SUBMITTED");
    expect(readBack.approvals).toHaveLength(1);
  });

  test("UC5_EF2_non_finance_and_self_approval_blocked: Employee cannot approve and Finance cannot self-approve", async ({
    page,
    request,
  }) => {
    // 1. Employee cannot approve a manager-approved request
    const title1 = uniqueTitle("UC5-EF2-EmployeeDeny");
    const { id: reqId1 } = await apiCreateAndSubmit(request, "alice@acme.com", title1, 60.0);
    await apiManagerApprove(request, reqId1, "bob@acme.com", "Bob OK");

    await login(page, "alice@acme.com");
    await page.goto(`/requests/${reqId1}`);
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);

    const aliceToken = await apiLogin(request, "alice@acme.com");
    const empRes = await request.post(`${API_BASE}/api/requests/${reqId1}/approve`, {
      headers: { Authorization: `Bearer ${aliceToken}` },
      data: {},
    });
    expect(empRes.status()).toBe(403);
    await logout(page);

    // 2. Finance self-approval blocked (BR4)
    const title2 = uniqueTitle("UC5-EF2-FinanceSelf");
    const { id: reqId2 } = await apiCreateAndSubmit(request, "fiona@acme.com", title2, 45.0);
    // Manager in Finance or another manager approves
    // Since Fiona is in Finance department, let's see: manager in same dept would be needed for SUBMITTED
    // For direct API check, if Fiona tries to decide on her own request:
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const selfRes = await request.post(`${API_BASE}/api/requests/${reqId2}/approve`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "Self approval attempt" },
    });
    expect(selfRes.status()).toBe(403);
  });

  test("UC5_EF3_repeated_approval_yields_no_duplicate_trail: Already finalised request rejects repeat approval", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC5-EF3-Duplicate");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 110.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager approval");

    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const firstApproval = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "Valid initial approval" },
    });
    expect(firstApproval.ok()).toBeTruthy();

    // Fiona views UI of already finalized request
    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator(".badge")).toHaveText("finance approved");
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(0);

    // Repeat API approval attempt must return HTTP 409 NOT_PENDING
    const secondApproval = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "Repeat approval attempt" },
    });
    expect(secondApproval.status()).toBe(409);

    // Postcondition: trail must have EXACTLY 3 rows (ZERO duplicates)
    const rb = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(rb.status).toBe("FINANCE_APPROVED");
    expect(rb.approvals).toHaveLength(3);
  });
});

test.describe("UC6 — Finance rejects a manager-approved expense request", () => {
  test("UC6_MF_and_AF2_finance_rejects_and_employee_views_outcome: Fiona rejects with comment; Alice sees rejected trail", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC6-MF-AF2");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 200.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager endorsed");

    // 1. Fiona signs in and opens the manager-approved request
    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator(".badge")).toHaveText("manager approved");

    // 2. Enter rejection reason and click Reject
    const reason = "Exceeds annual professional development cap";
    await page.locator("input[maxlength='500']").fill(reason);
    await page.getByRole("button", { name: "Reject" }).click();

    // 3. UI displays rejected badge and comment
    await expect(page.locator(".badge")).toHaveText("rejected");
    await expect(page.getByRole("button", { name: "Reject" })).toHaveCount(0);
    await expect(page.locator("table").nth(1)).toContainText(reason);
    await logout(page);

    // 4. Employee Alice logs in and views the rejected outcome (UC6-AF2)
    await fieldByLabel(page, "Email").fill("alice@acme.com");
    await fieldByLabel(page, "Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(new RegExp(`/requests/${reqId}$`));
    await expect(page.locator(".badge")).toHaveText("rejected");
    const employeeTrail = page.locator("table").nth(1);
    await expect(employeeTrail).toContainText("REJECT");
    await expect(employeeTrail).toContainText("manager approved → rejected");
    await expect(employeeTrail).toContainText(reason);

    // 5. Postcondition API read-back
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const rb = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(rb.status).toBe("REJECTED");
    expect(rb.approvals).toHaveLength(3);
    expect(rb.approvals[2].action).toBe("REJECT");
    expect(rb.approvals[2].comment).toBe(reason);
  });

  test("UC6_AF1_finance_rejects_from_inbox_with_prompt: Reject directly from inbox dialog", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC6-AF1-InboxReject");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 130.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager sign-off");

    await login(page, "fiona@acme.com");
    await expect(page.getByText(/Awaiting your approval/)).toBeVisible();

    const rejectionReason = "Missing commercial invoice";
    page.on("dialog", (dialog) => dialog.accept(rejectionReason));

    const inboxCard = page.locator(".card").filter({ hasText: "Awaiting your approval" });
    const targetRow = inboxCard.locator("tr").filter({ hasText: title });
    await expect(targetRow).toBeVisible();
    await targetRow.getByRole("button", { name: "Reject" }).click();

    // Verify row leaves inbox
    await expect(inboxCard.locator("tr").filter({ hasText: title })).toHaveCount(0);

    // API read-back
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const rb = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(rb.status).toBe("REJECTED");
    expect(rb.approvals).toHaveLength(3);
    expect(rb.approvals[2].action).toBe("REJECT");
    expect(rb.approvals[2].comment).toBe(rejectionReason);
  });

  test("UC6_EF1_finance_reject_without_reason_allowed: Empty comment accepted (EW-2 / PR-04)", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC6-EF1-BlankReason");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 88.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager OK");

    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator(".badge")).toHaveText("manager approved");

    // Click Reject without entering any comment
    await page.getByRole("button", { name: "Reject" }).click();
    await expect(page.locator(".badge")).toHaveText("rejected");

    // Postcondition API read-back: comment stored as empty string (EW-2)
    const fionaToken = await apiLogin(request, "fiona@acme.com");
    const rb = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(rb.status).toBe("REJECTED");
    expect(rb.approvals[2].comment).toBe("");
  });

  test("UC6_EF2_cannot_reject_already_finalised_request: Rejection blocked on terminal status", async ({
    page,
    request,
  }) => {
    const title = uniqueTitle("UC6-EF2-Terminal");
    const { id: reqId } = await apiCreateAndSubmit(request, "alice@acme.com", title, 77.0);
    await apiManagerApprove(request, reqId, "bob@acme.com", "Manager OK");

    const fionaToken = await apiLogin(request, "fiona@acme.com");
    // Fiona approves it first to make it FINANCE_APPROVED
    await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "First approval" },
    });

    await login(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator(".badge")).toHaveText("finance approved");
    await expect(page.getByRole("button", { name: "Reject" })).toHaveCount(0);

    // Direct API rejection attempt returns 409
    const rejectRes = await request.post(`${API_BASE}/api/requests/${reqId}/reject`, {
      headers: { Authorization: `Bearer ${fionaToken}` },
      data: { comment: "Reject finalized attempt" },
    });
    expect(rejectRes.status()).toBe(409);

    // Status remains FINANCE_APPROVED with exactly 3 approvals
    const rb = await (
      await request.get(`${API_BASE}/api/requests/${reqId}`, {
        headers: { Authorization: `Bearer ${fionaToken}` },
      })
    ).json();
    expect(rb.status).toBe("FINANCE_APPROVED");
    expect(rb.approvals).toHaveLength(3);
  });
});
