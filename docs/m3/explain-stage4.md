# Stage 4 Explanation: Performance and Recovery Testing

**Author:** Member 3 (roll no. 24i-0761, Section C)  
**Date:** November 2026  
**Audience:** Beginner / Peer Reviewers / Viva Examination Panel  

---

## 1. What Was Done and Why

In Stage 4, we evaluated the non-functional qualities of the Expense Approval MIS under load and during infrastructure disruption:
1. **Pre-test Limit Formulation:** Before running any test, we selected `GET /api/requests` as our target operation and formulated concrete Service Level Agreements (SLAs):
   - $T_{p95} \le 250\text{ ms}$
   - Unexpected failure rate $\le 0.1\%$
   - Justification: `GET /api/requests` is the highest-volume, read-heavy query in the application. It exercises database querying, role-based departmental filtering, and JSON object mapping.
2. **k6 Load Testing Across 4 Iterations:**
   - Run 1 (1 VU for 60s): Baseline single-user load.
   - Run 2 (1 VU for 60s): Single-user reproducibility replicate.
   - Run 3 (5 VUs for 60s): Concurrent multi-user load.
   - Run 4 (5 VUs for 60s): Multi-user reproducibility replicate.
   - Every single run lasted the full 60 seconds of sustained constant load, recording request count, throughput, p90, p95, and failure rates.
3. **Automated Failure and Recovery Testing:**
   - Created an automated Playwright test (`tests/team/perf/recovery.spec.ts`) that simulates a database infrastructure outage during an expense request approval.
   - Validated transaction atomicity, connection pool recovery, retry handling, and asserted that **exactly zero duplicate approval-trail rows** were created.

---

## 2. What Each Test Asserts

### 2.1 k6 Load Tests (`tests/team/perf/test_requests_perf.js`)
- `status is 200`: Asserts each request receives HTTP 200 OK.
- `has content`: Asserts the returned payload is valid JSON and contains a populated `content` array.
- `p(95) <= 250`: Asserts that 95% of all requests complete within 250 ms.
- `rate <= 0.001`: Asserts that failed requests remain under 0.1%.

### 2.2 Automated Recovery Spec (`tests/team/perf/recovery.spec.ts`)
1. **Initial Submission Check:** Alice creates and submits a request; asserts status is `SUBMITTED` with exactly 1 audit row (`action: SUBMIT`).
2. **Outage Simulation Check:** The PostgreSQL container is stopped; an approval attempt is made and asserts that the transition fails cleanly (`failedTransition === true`).
3. **Restoration & Rollback Check:** The database is restarted; read-back asserts the record did not suffer a partial write (no orphaned approval rows).
4. **Retry & Audit Trail Integrity:** The approval action is executed after recovery and asserts status is `MANAGER_APPROVED`.
5. **Zero Duplicate Row Assertion:** Explicitly filters all records with `action === 'APPROVE'` in the audit trail and asserts `approveActions.length === 1`. Exactly **0 duplicate approval rows** are persisted.

---

## 3. What Each Tool Output Means

### 3.1 k6 Summary Metrics
- **`http_req_duration (p95)`:** The 95th percentile response time. Across our runs, $T_{p95}$ ranged from **13.12 ms to 19.19 ms**, vastly beating the 250 ms SLA target.
- **`http_reqs (Throughput)`:** Requests served per second. Scaled linearly from **16.31 req/s** at 1 VU to **78.08 req/s** at 5 VUs (~4.7x speedup).
- **`http_req_failed`:** Percentage of non-2xx/3xx HTTP responses. Recorded **0.00%** across all 11,318 requests.
- **`iteration_duration`:** Average roundtrip cycle time for a virtual user, including network request and sleep delay (~60 ms).

### 3.2 Spring Boot Transaction Rollback Log
When the database container was stopped, Spring's `JpaTransactionManager` encountered `java.sql.SQLException: Connection is closed` and HikariCP connection pool logged connection validation errors. The transaction coordinator aborted the transaction, guaranteeing that partial memory states were not committed to the database.

---

## 4. 5 Likely Viva Questions and Concise Answers

### Q1: Why did you test `GET /api/requests` instead of a write operation like `POST /api/requests` for the 60-second k6 load test?
**Answer:** In an enterprise approval workflow, read operations (inbox viewing, status checking, list filtering) occur at least 10–50 times more frequently than creations. Load-testing a write endpoint for 4 minutes of sustained traffic would flood the database with over 10,000 artificial records, polluting production data and triggering sequential ID inflation. `GET /api/requests` tests relational joins, sorting, and authorization scoping safely and repeatably.

### Q2: What is the significance of the p95 metric compared to the average (mean) latency?
**Answer:** The average response time conceals outliers caused by garbage collection, thread scheduling, or connection pool contention. The 95th percentile ($p95$) guarantees that 95% of user requests experience latency at or below that threshold, providing a much truer measure of real-world user experience and tail latency.

### Q3: How did the system perform when scaling from 1 Virtual User to 5 Virtual Users?
**Answer:** Throughput scaled almost linearly from ~16.4 req/s to ~77.6 req/s (~4.7x increase), while the p95 latency only increased modestly from 16.78 ms to 19.19 ms (+2.41 ms). This proves that the Spring Boot Tomcat thread pool and PostgreSQL query planner handle concurrent readers with minimal lock contention.

### Q4: In the failure-and-recovery test, how did you verify that no partial write occurred?
**Answer:** In the database schema, an expense request transition updates the `expense_request` table's `status` column and inserts a record into the `approval` table. If the database crashes mid-operation, atomicity dictates both writes must succeed or neither. We verified this by checking that after the outage, the status remained `SUBMITTED` and the approval trail row count remained exactly 1 (no orphaned approval rows).

### Q5: How did you assert zero duplicate approval-trail rows?
**Answer:** In `tests/team/perf/recovery.spec.ts`, after recovering the database and retrying the approval, we queried the full audit trail via `GET /api/requests/{id}` and filtered the array for entries where `action === 'APPROVE'`. We asserted `approveActions.length === 1`. If the retry had created a duplicate entry alongside the failed attempt, this count would have been $\ge 2$.
