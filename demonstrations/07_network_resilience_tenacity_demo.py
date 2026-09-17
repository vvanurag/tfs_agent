"""
=============================================================================
DEMO 7: NETWORK RESILIENCE & RETRY WITH EXPONENTIAL BACKOFF (TENACITY)
=============================================================================
Core Capability:
  - Using the Tenacity library to automatically recover from transient failures.
  - Adding jittered exponential backoff for HTTP 500, 503, 429, and timeouts.
=============================================================================
"""

import time
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

# Configure logger to display retry attempts
logging.basicConfig(level=logging.INFO, format="   [Resilience Gateway] %(message)s")
logger = logging.getLogger("TenacityDemo")


class TransientNetworkError(Exception):
    """Simulated transient server failure (e.g. 503 Service Unavailable)."""
    pass


# Global attempt counter for simulation
simulated_failure_count = 0

# ---------------------------------------------------------------------------
# RESILIENT FUNCTION WITH JITTERED EXPONENTIAL BACKOFF
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception_type(TransientNetworkError),
    stop=stop_after_attempt(4),  # Retry up to 4 times total
    wait=wait_random_exponential(multiplier=0.5, max=5),  # Exponential backoff + random jitter
    reraise=True
)
def fetch_data_with_retry(endpoint: str):
    global simulated_failure_count
    simulated_failure_count += 1
    
    print(f"\n--> [HTTP Request] Attempt #{simulated_failure_count} to {endpoint}...")
    
    # Simulate failures on attempts 1 and 2, then succeed on attempt 3
    if simulated_failure_count < 3:
        print(f"    ❌ HTTP 503: Service Temporarily Unavailable (Attempt {simulated_failure_count})")
        raise TransientNetworkError("Temporary 503 Service Unavailable")
        
    print(f"    ✅ HTTP 200 OK: Data successfully received on Attempt #{simulated_failure_count}!")
    return {"status": "success", "work_items": [10241, 10242, 10243]}


def demonstrate_network_resilience():
    global simulated_failure_count
    simulated_failure_count = 0

    print("=" * 65)
    print("DEMO 7: NETWORK RESILIENCE GATEWAY (TENACITY + BACKOFF)")
    print("=" * 65)
    print("Simulating an API that fails twice with transient 503 errors,")
    print("then automatically recovers without crashing the pipeline.\n")

    start_time = time.time()
    try:
        result = fetch_data_with_retry("https://tfs.enterprise.local/_apis/wit/workitems")
        elapsed = time.time() - start_time
        print(f"\n🎉 Pipeline Execution Succeeded in {elapsed:.2f}s!")
        print(f"Result Payload: {result}")
    except Exception as e:
        print(f"\n❌ Pipeline failed after all retry attempts: {e}")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    demonstrate_network_resilience()
