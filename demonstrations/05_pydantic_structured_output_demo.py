"""
=============================================================================
DEMO 5: TYPE-SAFE STRUCTURED OUTPUT WITH PYDANTIC & LLAMA 3
=============================================================================
Core Capability:
  - Forcing real LLMs to output strongly-typed, validated Python objects.
  - Using `llm.with_structured_output(PydanticSchema)` to eliminate malformed JSON.
=============================================================================
"""

from pydantic import BaseModel, Field
from typing import List
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 1. DEFINE DESIRED OUTPUT SCHEMA
# ---------------------------------------------------------------------------
class WorkItemAnalysis(BaseModel):
    ticket_id: int = Field(description="The numeric work item ticket ID")
    title: str = Field(description="Summary title of the issue")
    severity: str = Field(description="'Critical', 'High', 'Medium', or 'Low'")
    root_cause: str = Field(description="Technical summary of the suspected root cause")
    remediation_steps: List[str] = Field(description="Ordered list of action items to fix the issue")

def demonstrate_structured_output():
    print("=" * 65)
    print("DEMO 5: PYDANTIC STRUCTURED OUTPUT FROM LLAMA 3")
    print("=" * 65)

    # 1. Initialize LLM and bind schema
    llm = ChatOllama(model="llama3", temperature=0.0)
    structured_llm = llm.with_structured_output(WorkItemAnalysis)

    # 2. Raw Unstructured Text Input
    raw_incident = """
    INCIDENT REPORT #10243:
    Backend engineer Alex Rivera reported that under peak API traffic, SQLite 
    database connection handles are exhausted because cursors are left open. 
    FastAPI requests are throwing 'OperationalError: database is locked'. 
    Severity is High. Remediation involves wrapping database operations in 
    context managers and setting check_same_thread=False with a 5000ms lease timeout.
    """

    print("Input Unstructured Incident Report:\n" + raw_incident.strip() + "\n")
    print("--> Invoking Llama 3 with Pydantic contract...")
    
    # Returns an actual instance of WorkItemAnalysis
    result: WorkItemAnalysis = structured_llm.invoke(raw_incident)

    print("\n✅ Successfully Parsed into Type-Safe Python Object:")
    print(f"  • Object Type       : {type(result)}")
    print(f"  • Ticket ID         : {result.ticket_id}")
    print(f"  • Title             : {result.title}")
    print(f"  • Severity          : {result.severity}")
    print(f"  • Root Cause        : {result.root_cause}")
    print(f"  • Remediation Steps :")
    for step in result.remediation_steps:
        print(f"     - {step}")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    demonstrate_structured_output()
