# Performance and Recovery Specification

**Author:** Member 3 (roll no. 24i-0761, Section C)  
**Date:** November 2026  
**Module:** Expense Requests Workflow  

---

## 1. Chosen Operation & Justification

### Selected Operation
- **Endpoint:** `GET /api/requests` (Scoped expense request listing with requester/department query)
- **HTTP Method:** `GET`
- **Authenticated User:** `bob@acme.com` (Engineering Manager)

### Justification
1. **High Frequency / Repeatable Read:** `GET /api/requests` is the primary read query invoked by users upon logging in, navigating between tabs, and refreshing the approval inbox. It represents the highest volume endpoint in the system.
2. **Database Joining & Scoping Complexity:** Unlike a simple health check or single-row key lookup, `GET /api/requests` executes a multi-table query with role-based scoping (filtering requests belonging to the manager's department, joining approval trails, and aggregating line item totals).
3. **Safe & Repeatable for Load Testing:** As a read-only query, it is non-destructive and produces consistent, repeatable load against the database and Spring Boot JPA connection pool without accumulating unbounded dummy records or exhausting primary key sequences during 60-second test iterations.

---

## 2. Pre-Execution Limits & Targets

Before running any k6 load tests, the following engineering targets are established based on the system architecture (Spring Boot 3 + PostgreSQL running in a containerized local environment):

| Metric | Target / Threshold | Justification |
|---|---|---|
| **p95 Latency ($T_{p95}$)** | **$\le$ 250 ms** | Internal enterprise applications expect sub-second responsiveness. For a scoped relational query with JPA object mapping on localhost, a 95th percentile under 250 ms guarantees a smooth user experience without UI stalling. |
| **p99 Latency ($T_{p99}$)** | **$\le$ 500 ms** | Accommodates occasional garbage collection (JVM ZGC/G1GC) pauses or connection pool checkout latency under concurrent load. |
| **Unexpected Failure Rate** | **$\le$ 0.1% (effectively 0%)** | For a stable read endpoint under mild concurrency (1 to 5 virtual users), any non-200 response (such as 500 Internal Server Error or connection drop) indicates a defect or resource exhaustion. |
| **Throughput (req/s)** | **$\ge$ 15 req/s (1 VU), $\ge$ 50 req/s (5 VU)** | Ensures the HTTP thread pool and embedded Tomcat server handle sustained concurrent requests efficiently. |

---

## 3. k6 Test Design & Execution Plan

- **Engine:** k6 v1.5.0 (Windows binary `C:\Program Files\k6\k6.exe`)
- **Execution Matrix:**
  1. **Run 1 (1 VU):** Sustained constant 1 Virtual User for 60 seconds.
  2. **Run 2 (1 VU):** Verification replicate with 1 Virtual User for 60 seconds.
  3. **Run 3 (5 VUs):** Sustained constant 5 Virtual Users for 60 seconds.
  4. **Run 4 (5 VUs):** Verification replicate with 5 Virtual Users for 60 seconds.
- **Reporting:** Each run exports raw console output and structured JSON summary to `evidence/m3/perf/`.

---

## 4. Empirical Test Results

Every single run was executed continuously for 60 seconds against the live Spring Boot backend (`http://localhost:8081`):

| Run ID | Concurrency (VUs) | Duration | Total Requests | Throughput (req/s) | p90 Latency | p95 Latency | Max Latency | Failure Rate | Result vs SLA |
|---|---|---|---|---|---|---|---|---|---|
| **Run 1** | 1 VU | 60s | 981 | 16.31 req/s | 13.91 ms | **16.78 ms** | 113.80 ms | **0.00%** (0/981) | **PASS** (p95 << 250ms SLA) |
| **Run 2** | 1 VU | 60s | 998 | 16.59 req/s | 11.74 ms | **13.12 ms** | 113.85 ms | **0.00%** (0/998) | **PASS** (p95 << 250ms SLA) |
| **Run 3** | 5 VUs | 60s | 4,638 | 77.10 req/s | 17.83 ms | **19.19 ms** | 99.58 ms | **0.00%** (0/4638) | **PASS** (p95 << 250ms SLA) |
| **Run 4** | 5 VUs | 60s | 4,701 | 78.08 req/s | 17.46 ms | **18.60 ms** | 137.26 ms | **0.00%** (0/4701) | **PASS** (p95 << 250ms SLA) |

### Key Findings & SLA Analysis
1. **Exceptional Latency Stability:** Across all 11,318 requests processed during the load tests, the p95 latency remained between **13.12 ms and 19.19 ms**, beating our pre-established SLA threshold of $\le 250\text{ ms}$ by more than an order of magnitude.
2. **Linear Concurrency Scaling:** Scaling from 1 VU to 5 VUs increased throughput from ~16.4 req/s to ~77.6 req/s (~4.7x scaling factor), demonstrating minimal lock contention on PostgreSQL and optimal thread utilization in Tomcat.
3. **Zero Unexpected Failures:** Across all runs, 0 requests failed (`http_req_failed` rate = 0.00%), satisfying our reliability criteria.

Raw logs and summaries are preserved in:
- Run 1 (1 VU): [`evidence/m3/perf/run1_1vu.txt`](../../evidence/m3/perf/run1_1vu.txt) and [`evidence/m3/perf/run1_1vu_summary.json`](../../evidence/m3/perf/run1_1vu_summary.json)
- Run 2 (1 VU): [`evidence/m3/perf/run2_1vu.txt`](../../evidence/m3/perf/run2_1vu.txt) and [`evidence/m3/perf/run2_1vu_summary.json`](../../evidence/m3/perf/run2_1vu_summary.json)
- Run 3 (5 VU): [`evidence/m3/perf/run3_5vu.txt`](../../evidence/m3/perf/run3_5vu.txt) and [`evidence/m3/perf/run3_5vu_summary.json`](../../evidence/m3/perf/run3_5vu_summary.json)
- Run 4 (5 VU): [`evidence/m3/perf/run4_5vu.txt`](../../evidence/m3/perf/run4_5vu.txt) and [`evidence/m3/perf/run4_5vu_summary.json`](../../evidence/m3/perf/run4_5vu_summary.json)

---

## 5. Automated Failure and Recovery Specification

### Objective
Verify that the Expense Request system adheres to ACID transactional boundaries during state-changing operations. Specifically, if a dependency fails or the application crashes mid-transaction (e.g., during database writing of an approval action), the transaction must roll back cleanly without leaving partial writes or orphaned records. Upon recovery and retry, the final state must contain **zero duplicate approval-trail rows**.

### Failure Injection Strategy & Test Results
- **Target Action:** Manager approval of a `SUBMITTED` request (`POST /api/requests/{id}/approve`).
- **Simulated Failure:** The PostgreSQL database container (`expense-approval-db-1`) is halted via Docker engine command while a state transition is dispatched.
- **Observed Behavior & Verification:**
  1. The uncommitted approval transaction fails to write to the offline database.
  2. Spring's `JpaTransactionManager` triggers rollback; the HikariCP connection pool logs validation warnings and cleans closed socket handles.
  3. The database container is restarted.
  4. Read-back verification proves **zero partial write** occurred (no orphaned approval entity without parent status update, or vice versa).
  5. The final state is read back: exactly 2 approval trail rows exist (1 `SUBMIT` row by Alice + 1 `APPROVE` row by Bob).
  6. **Duplicate Row Assertion:** Filtered count of `APPROVE` actions in the audit trail is exactly **1**. Exactly **0 duplicate approval-trail rows** were created.

The automated test is implemented in [`tests/team/perf/recovery.spec.ts`](../../tests/team/perf/recovery.spec.ts) and passed cleanly in 8.6s. Raw console execution log is saved in [`evidence/m3/perf/recovery-test-log.txt`](../../evidence/m3/perf/recovery-test-log.txt).
