# Adjudication Service & Core Engine Architecture Specification

## 1. NTLM Handshake Timeout Remediation & SLA Policy
* **SLA Rule 4.2.1:** All NTLM authentication handshakes against legacy Active Directory services must incorporate **jittered exponential backoff**.
* **Retry Strategy:**
  - Maximum retries: 3 attempts.
  - Initial delay: 500ms with a multiplier of 2.0.
  - Random jitter: ±150ms to prevent thundering herd spikes against domain controllers.
  - Hard timeout ceiling: 30,000ms.
* **Network Failover:** If transient 500 or 503 errors persist after 3 retries, the pipeline must route the request through the local Resilience Gateway and log an incident ticket.

## 2. Database Connection Pooling & SQLite Concurrency
* **Architecture Standard:** When running local SQLite instances under concurrent FastAPI workers, the database handle must be instantiated with `check_same_thread=False`.
* **Lease Timeout:** Database connection lease timeout must not exceed 5000ms.
* **Cursor Cleanup:** All cursor executions must be wrapped in `try...finally` context managers to prevent uncollected memory buildup.

## 3. Batch Claim Processing Throughput & Lock Management
* **Batch Processing SLA:** Batch claim processing must complete within a strict 15-minute window.
* **Concurrency Cap:** A maximum of 8 worker threads may process claims simultaneously to prevent row-level table lock contention in the SQLite status ledger.
