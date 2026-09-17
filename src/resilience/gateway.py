"""
=============================================================================
STAGE 4: NETWORK RESILIENCE GATEWAY (TENACITY RETRY & EXPONENTIAL BACKOFF)
=============================================================================
Provides automated retry policies with random jitter and exponential backoff
for HTTP requests and API connectors.
=============================================================================
"""

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger("ResilienceGateway")

# Transient exceptions to retry
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.HTTPError
)

def is_retryable_http_error(exception: BaseException) -> bool:
    """Checks if an HTTP error is transient (500, 502, 503, 504, 429)."""
    if isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exception, requests.exceptions.HTTPError):
        if exception.response is not None:
            return exception.response.status_code in [429, 500, 502, 503, 504]
    return False


@retry(
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=0.5, max=5),
    reraise=True
)
def resilient_request(method: str, url: str, **kwargs) -> requests.Response:
    """
    Executes an HTTP request with automatic jittered exponential backoff retry.
    """
    response = requests.request(method=method, url=url, timeout=kwargs.pop("timeout", 10), **kwargs)
    response.raise_for_status()
    return response


class ResilienceGateway:
    """
    Gateway wrapper providing hardened, fault-tolerant HTTP operations.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return resilient_request("GET", url, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return resilient_request("POST", url, **kwargs)
