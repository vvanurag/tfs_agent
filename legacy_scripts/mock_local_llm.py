import json

class MockMessage:
    def __init__(self, content: str):
        self.content = content

class MockChoice:
    def __init__(self, content: str):
        self.message = MockMessage(content)

class MockCompletionResponse:
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]

class MockCompletions:
    def create(self, model: str = "gpt-4o", messages: list = None, **kwargs):
        """
        Simulates an LLM response without network egress.
        Returns a structured sprint report JSON string.
        """
        # Simulated LLM output
        mock_report = {
            "sprint_id": "Sprint 12",
            "overall_status": "At Risk",
            "active_bugs_count": 4,
            "critical_blockers": [
                "NTLM Handshake Timeout Exception in Adjudication Service (#10241)",
                "SLA Breach on Adjudication Batch Pipeline (#10251)"
            ],
            "architecture_remediations": [
                "Apply jittered exponential backoff (3 retries, 500ms delay) per SLA Rule 4.2.1",
                "Cap batch claim concurrency at 8 worker threads to avoid SQLite lock contention"
            ],
            "sla_risk_summary": "Claims processing SLA breached; NTLM domain controller timeouts require immediate resilience failover."
        }
        return MockCompletionResponse(json.dumps(mock_report))

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    """
    Zero-Egress in-memory LLM simulator.
    Mimics the OpenAI / LangChain client interface for offline unit testing.
    """
    def __init__(self, api_key: str = "mock-key", **kwargs):
        self.chat = MockChat()
