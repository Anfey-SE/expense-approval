import { test, expect } from "@playwright/test";
import { execSync } from "child_process";

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

async function createAndSubmitRequest(token: string, title: string) {
  const res = await fetch(`${API_BASE}/api/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      title,
      description: "Failure and Recovery verification request",
      currency: "USD",
      items: [
        {
          description: "Database Interruption Test Item",
          category: "Other",
          amount: 300.0,
          incurredOn: new Date().toISOString().slice(0, 10),
        },
      ],
    }),
  });
  if (!res.ok) throw new Error("Failed to create expense request");
  const data = await res.json();
  const reqId = data.id as number;

  const subRes = await fetch(`${API_BASE}/api/requests/${reqId}/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!subRes.ok) throw new Error(`Failed to submit request ${reqId}`);
  return reqId;
}

test.describe("Automated Failure and Recovery Tests", () => {
  test("State transition atomicity during dependency failure and clean recovery with zero duplicate approval-trail rows", async ({
    request,
  }) => {
    console.log("1. Setting up fresh request for recovery test...");
    const aliceToken = await loginViaApi("alice@acme.com");
    const bobToken = await loginViaApi("bob@acme.com");
    const reqId = await createAndSubmitRequest(aliceToken, `Recovery-Test-${Date.now()}`);

    // Verify initial submitted state
    const initRes = await request.get(`${API_BASE}/api/requests/${reqId}`, {
      headers: { Authorization: `Bearer ${bobToken}` },
    });
    expect(initRes.status()).toBe(200);
    const initData = await initRes.json();
    expect(initData.status).toBe("SUBMITTED");
    expect(initData.approvals.length).toBe(1); // Exactly 1: SUBMIT action
    console.log(`Initial state confirmed: ${initData.status}, trail rows: ${initData.approvals.length}`);

    // 2. Simulate Dependency Failure (Stop database container completely before state transition is dispatched)
    console.log("2. Simulating dependency failure: stopping postgres container 'expense-approval-db-1'...");
    execSync("docker stop expense-approval-db-1", { stdio: "pipe" });

    // Ensure container is truly stopped
    const isRunning = execSync('docker inspect -f "{{.State.Running}}" expense-approval-db-1').toString().trim();
    console.log(`PostgreSQL container running status: ${isRunning}`);
    expect(isRunning).toBe("false");

    console.log("3. Attempting state transition (approval) while database container is offline...");
    let failedTransition = false;
    let failStatus = 0;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const failRes = await fetch(`${API_BASE}/api/requests/${reqId}/approve`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${bobToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ comment: "Approve during simulated outage" }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      failStatus = failRes.status;
      if (!failRes.ok) failedTransition = true;
    } catch (err) {
      failedTransition = true;
      console.log("Observed expected dependency failure during state transition attempt:", (err as Error).message);
    }
    expect(failedTransition).toBe(true);

    // 3. Restore dependency (Restart PostgreSQL container)
    console.log("4. Restoring dependency: restarting postgres container 'expense-approval-db-1'...");
    execSync("docker start expense-approval-db-1", { stdio: "pipe" });

    // Wait 5 seconds for PostgreSQL to accept socket connections and Spring Boot HikariCP pool to recover
    await new Promise((r) => setTimeout(r, 5000));

    // 4. Inspect persisted state after dependency recovery
    console.log("5. Inspecting state after recovery...");
    const checkRes = await request.get(`${API_BASE}/api/requests/${reqId}`, {
      headers: { Authorization: `Bearer ${bobToken}` },
    });
    expect(checkRes.status()).toBe(200);
    const checkData = await checkRes.json();
    console.log(`Persisted status after recovery: ${checkData.status}, approvals: ${checkData.approvals.length}`);

    // If the transaction failed, execute retry; if Hikari buffered and replayed, verify audit trail integrity
    if (checkData.status === "SUBMITTED") {
      console.log("Atomic rollback confirmed (no partial write). Retrying approval...");
      const retryRes = await request.post(`${API_BASE}/api/requests/${reqId}/approve`, {
        headers: {
          Authorization: `Bearer ${bobToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ comment: "Bob approved post-recovery" }),
      });
      expect(retryRes.status()).toBe(200);
    } else {
      console.log("Connection was committed or recovered automatically by persistence layer.");
    }

    // 5. Final Read-back Assertion: Check exact approval trail count and zero duplicate rows
    console.log("6. Final read-back verification of approval trail...");
    const finalRes = await request.get(`${API_BASE}/api/requests/${reqId}`, {
      headers: { Authorization: `Bearer ${bobToken}` },
    });
    expect(finalRes.status()).toBe(200);
    const finalData = await finalRes.json();
    expect(finalData.status).toBe("MANAGER_APPROVED");

    // Check approval trail integrity
    console.log("Approval trail records:", finalData.approvals);
    // Row 0: SUBMIT (draft -> submitted)
    // Row 1: APPROVE (submitted -> manager_approved)
    expect(finalData.approvals.length).toBe(2);
    expect(finalData.approvals[0].action).toBe("SUBMIT");
    expect(finalData.approvals[1].action).toBe("APPROVE");
    expect(finalData.approvals[1].actorName).toBe("Bob Manager");

    // Explicit check for zero duplicate approval actions
    const approveActions = finalData.approvals.filter((a: any) => a.action === "APPROVE");
    expect(approveActions.length).toBe(1);
    console.log("Recovery test PASSED: Exactly 0 duplicate approval-trail rows created!");
  });
});
