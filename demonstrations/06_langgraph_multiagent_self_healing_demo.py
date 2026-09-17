"""
=============================================================================
DEMO 6: LANGGRAPH MULTI-AGENT STATE GRAPH & SELF-HEALING LOOP
=============================================================================
Core Capability:
  - Designing a stateful multi-agent workflow using LangGraph StateGraph.
  - Passing state between specialized agents (Drafting -> Validation -> Correction).
  - Automatically catching formatting/JSON errors and self-healing.
=============================================================================
"""

import json
import re
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 1. GRAPH STATE & PYDANTIC SCHEMA
# ---------------------------------------------------------------------------
class SprintReportSchema(BaseModel):
    sprint_id: str = Field(description="Sprint name e.g. 'Sprint 12'")
    status: str = Field(description="'On Track', 'At Risk', or 'Blocked'")
    critical_blockers: List[str] = Field(description="List of critical blocker titles")
    remediation_summary: str = Field(description="Summary of remediation actions")

class AgentState(TypedDict):
    messages: List[str]
    report_draft: str
    validation_errors: Optional[str]
    retry_count: int
    final_report: Optional[dict]


# ---------------------------------------------------------------------------
# 2. SPECIALIZED NODES
# ---------------------------------------------------------------------------
def drafting_node(state: AgentState) -> AgentState:
    """Drafts report using local Llama 3."""
    print("\n-> [Node 1: Drafting Agent] Prompting Llama 3 to draft JSON...")
    llm = ChatOllama(model="llama3", temperature=0.1)
    
    prompt = f"""You are a DevOps assistant. Create a JSON report for this task:
{state['messages'][0]}

Output ONLY a JSON object with:
- sprint_id: (e.g. 'Sprint 12')
- status: ('On Track' or 'At Risk')
- critical_blockers: (list of strings)
- remediation_summary: (string)
"""
    response = llm.invoke(prompt)
    content = re.sub(r"^```json\s*|^```\s*|\s*```$", "", response.content.strip())
    state["report_draft"] = content
    return state


def validation_node(state: AgentState) -> AgentState:
    """Validates output against Pydantic schema."""
    print("-> [Node 2: Validation Agent] Enforcing SprintReportSchema contract...")
    try:
        data = json.loads(state["report_draft"])
        validated = SprintReportSchema.model_validate(data)
        state["final_report"] = validated.model_dump()
        state["validation_errors"] = None
        print("   ✅ Validation PASSED!")
    except Exception as e:
        state["validation_errors"] = str(e)
        print(f"   ❌ Validation FAILED: {state['validation_errors'][:60]}...")
    return state


def correction_node(state: AgentState) -> AgentState:
    """Self-Healing Loop: Reprompts Llama 3 with exact validation error."""
    state["retry_count"] += 1
    print(f"-> [Node 3: Correction Agent] SELF-HEALING (Attempt {state['retry_count']}/3)...")
    
    llm = ChatOllama(model="llama3", temperature=0.0)
    prompt = f"""Fix the validation error in this JSON:
ERROR: {state['validation_errors']}
PREVIOUS DRAFT: {state['report_draft']}

Output ONLY valid JSON with 'sprint_id', 'status', 'critical_blockers', and 'remediation_summary'.
"""
    response = llm.invoke(prompt)
    content = re.sub(r"^```json\s*|^```\s*|\s*```$", "", response.content.strip())
    state["report_draft"] = content
    return state


def router(state: AgentState) -> str:
    """Conditional Edge: Routes to Correction if invalid, or END if valid."""
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print("   [Router] Routing -> Correction Agent.")
        return "correction"
    print("   [Router] Routing -> END.")
    return "end"


# ---------------------------------------------------------------------------
# 3. BUILD & COMPILE GRAPH
# ---------------------------------------------------------------------------
def demonstrate_langgraph():
    print("=" * 65)
    print("DEMO 6: LANGGRAPH MULTI-AGENT STATE GRAPH WITH SELF-HEALING")
    print("=" * 65)

    workflow = StateGraph(AgentState)
    workflow.add_node("drafting", drafting_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("correction", correction_node)

    workflow.set_entry_point("drafting")
    workflow.add_edge("drafting", "validation")
    workflow.add_conditional_edges("validation", router, {"correction": "correction", "end": END})
    workflow.add_edge("correction", "validation")

    app = workflow.compile()

    initial_state = {
        "messages": ["Sprint 12 status report: NTLM timeouts on authentication and SQLite lock errors."],
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0,
        "final_report": None
    }

    final_state = app.invoke(initial_state)
    
    print("\n" + "=" * 65)
    print("FINAL VALIDATED SPRINT REPORT:")
    print("=" * 65)
    print(json.dumps(final_state["final_report"], indent=2))


if __name__ == "__main__":
    demonstrate_langgraph()
