import { test, expect } from "@playwright/test";

const API_BASE = "http://localhost:8081";

async function loginViaApi(email: string, password = "password123") {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`API login failed for ${email}`);
  const data = await res.json();
  return data.token;
}

async function createExpenseRequest(token: string, title: string) {
  const res = await fetch(`${API_BASE}/api/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      title,
      description: "Security test request",
      currency: "USD",
      items: [
        {
          description: "Flight Ticket",
          category: "Travel",
          amount: 250.0,
          incurredOn: new Date().toISOString().slice(0, 10),
        },
      ],
    }),
  });
  if (!res.ok) throw new Error("Failed to create expense request");
  const data = await res.json();
  return data.id as number;
}

async function submitExpenseRequest(token: string, reqId: number) {
  const res = await fetch(`${API_BASE}/api/requests/${reqId}/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to submit request ${reqId}`);
}

async function loginViaUi(page: any, email: string) {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill("password123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(new RegExp("http://localhost:5173/?$"));
}

test.describe("Security Access Control Decisions Matrix Tests", () => {
  // Decision 1: ALLOWED - Manager Same Dept Approves Submitted Request
  test("Decision 1 (Allowed): Manager Same Department can approve a submitted request", async ({
    page,
    request,
  }) => {
    const aliceToken = await loginViaApi("alice@acme.com");
    const bobToken = await loginViaApi("bob@acme.com"); // Bob is Engineering Manager (same as Alice)
    const reqId = await createExpenseRequest(aliceToken, `SecTest Decision1 ${Date.now()}`);
    await submitExpenseRequest(aliceToken, reqId);

    // 1. Direct API Verification (Allowed)
    const apiRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: {
        Authorization: `Bearer ${bobToken}`,
        "Content-Type": "application/json",
      },
      data: { comment: "Bob approves engineering request" },
    });
    expect(apiRes.status()).toBe(200);
    const body = await apiRes.json();
    expect(body.status).toBe("MANAGER_APPROVED");

    // 2. UI Verification
    await loginViaUi(page, "bob@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator("body")).toContainText(/manager approved/i);
    await expect(page.locator("body")).toContainText("Bob approves engineering request");
  });

  // Decision 2: DENIED - Manager Other Dept Attempts Approval
  test("Decision 2 (Denied): Manager from different department is blocked from approving request", async ({
    page,
    request,
  }) => {
    const aliceToken = await loginViaApi("alice@acme.com"); // Engineering
    const daveToken = await loginViaApi("dave@acme.com"); // Sales Manager (other dept)
    const reqId = await createExpenseRequest(aliceToken, `SecTest Decision2 ${Date.now()}`);
    await submitExpenseRequest(aliceToken, reqId);

    // 1. Direct API Verification (Denied - 403 Forbidden)
    const apiRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: {
        Authorization: `Bearer ${daveToken}`,
        "Content-Type": "application/json",
      },
      data: { comment: "Dave attempts cross-department approval" },
    });
    expect(apiRes.status()).toBe(403);
    const errorBody = await apiRes.json();
    expect(errorBody.code).toBe("FORBIDDEN");
    expect(errorBody.message).toContain("You can only decide on requests in your own department");

    // 2. UI Verification (Dave cannot view/approve Alice's request)
    await loginViaUi(page, "dave@acme.com");
    await page.goto(`/requests/${reqId}`);
    // Service returns 404 to avoid leaking cross-dept request info, UI renders error banner
    await expect(page.locator(".error")).toContainText("Request not found");
    await expect(page.getByRole("button", { name: "Approve" })).not.toBeVisible();
  });

  // Decision 3: DENIED - Other Employee Cannot View or Edit Another Employee's Request
  test("Decision 3 (Denied): Other employee cannot view or edit draft request", async ({
    page,
    request,
  }) => {
    const aliceToken = await loginViaApi("alice@acme.com");
    const carolToken = await loginViaApi("carol@acme.com"); // Carol is Employee in Sales
    const reqId = await createExpenseRequest(aliceToken, `SecTest Decision3 ${Date.now()}`);

    // 1. Direct API Verification (Denied - 404 on GET, 403 on PUT)
    const getRes = await request.get(`${API_BASE}/api/requests/${reqId}`, {
      headers: { Authorization: `Bearer ${carolToken}` },
    });
    expect(getRes.status()).toBe(404);

    const putRes = await request.put(`${API_BASE}/api/requests/${reqId}`, {
      headers: {
        Authorization: `Bearer ${carolToken}`,
        "Content-Type": "application/json",
      },
      data: {
        title: "Tampered Title by Carol",
        items: [
          {
            description: "Tampered item",
            category: "Other",
            amount: 500.0,
            incurredOn: new Date().toISOString().slice(0, 10),
          },
        ],
      },
    });
    expect(putRes.status()).toBe(403);
    const putErr = await putRes.json();
    expect(putErr.message).toContain("You can only edit your own requests");

    // 2. UI Verification (Carol sees Request not found and cannot edit)
    await loginViaUi(page, "carol@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator(".error")).toContainText("Request not found");
  });

  // Decision 4: ALLOWED - Finance User Approves Manager-Approved Request
  test("Decision 4 (Allowed): Finance user can approve a manager-approved request", async ({
    page,
    request,
  }) => {
    const aliceToken = await loginViaApi("alice@acme.com");
    const bobToken = await loginViaApi("bob@acme.com");
    const fionaToken = await loginViaApi("fiona@acme.com");

    const reqId = await createExpenseRequest(aliceToken, `SecTest Decision4 ${Date.now()}`);
    await submitExpenseRequest(aliceToken, reqId);

    // Transition to MANAGER_APPROVED by Bob
    await fetch(`${API_BASE}/api/requests/${reqId}/approve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${bobToken}`,
      },
      body: JSON.stringify({ comment: "Manager approved" }),
    });

    // 1. Direct API Verification (Allowed - 200 OK)
    const apiRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: {
        Authorization: `Bearer ${fionaToken}`,
        "Content-Type": "application/json",
      },
      data: { comment: "Finance approved and verified" },
    });
    expect(apiRes.status()).toBe(200);
    const body = await apiRes.json();
    expect(body.status).toBe("FINANCE_APPROVED");

    // 2. UI Verification
    await loginViaUi(page, "fiona@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator("body")).toContainText(/finance approved/i);
    await expect(page.locator("body")).toContainText("Finance approved and verified");
  });

  // Decision 5: DENIED - Employee Owner Cannot Approve Own Request (Self-Approval Prevention)
  test("Decision 5 (Denied): Requester is blocked from self-approving their own expense request", async ({
    page,
    request,
  }) => {
    const aliceToken = await loginViaApi("alice@acme.com");
    const reqId = await createExpenseRequest(aliceToken, `SecTest Decision5 ${Date.now()}`);
    await submitExpenseRequest(aliceToken, reqId);

    // 1. Direct API Verification (Denied - 403 Forbidden)
    const apiRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
      headers: {
        Authorization: `Bearer ${aliceToken}`,
        "Content-Type": "application/json",
      },
      data: { comment: "Alice tries to self-approve" },
    });
    expect(apiRes.status()).toBe(403);
    const errBody = await apiRes.json();
    expect(errBody.code).toBe("FORBIDDEN");

    // 2. UI Verification (Alice does not see decision card/buttons)
    await loginViaUi(page, "alice@acme.com");
    await page.goto(`/requests/${reqId}`);
    await expect(page.locator("body")).toContainText(/submitted/i);
    await expect(page.getByRole("button", { name: "Approve" })).not.toBeVisible();
    await expect(page.getByRole("button", { name: "Reject" })).not.toBeVisible();
  });
});
