from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from mock_local_llm import MockClient

# ---------------------------------------------------------
# 1. SETUP GRAPH STATE
# ---------------------------------------------------------
class AgentState(TypedDict):
    """
    Tracks the state of our multi-agent workflow.
    """
    messages: List[str]
    report_draft: str
    validation_errors: str
    retry_count: int

# ---------------------------------------------------------
# 2. IMPLEMENT SPECIALIZED NODES
# ---------------------------------------------------------
""" def drafting_agent(state: AgentState):
    ""Generates the structured project update report.""
    print("-> [Node: Drafting Agent] Synthesizing data into a report draft...")
    # In production, this invokes your LLM with the TFS and RAG tools
    state["report_draft"] = '{"sprint_id": "Sprint 12", "status": "At Risk", "blockers": "NTLM Timeouts"}'
    return state """
def drafting_agent(state: AgentState):
    """Generates the structured project update report using the Mock LLM."""
    print("-> [Node: Drafting Agent] Synthesizing data into a report draft...")
    
    # Initialize our zero-egress LLM simulator
    llm_client = MockClient()
    
    # Invoke the mock LLM instead of using a hardcoded string
    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "\n".join(state["messages"])}]
    )

    state["report_draft"] = response.choices[0].message.content
    return state

def validation_agent(state: AgentState):
    """Checks if required fields are present in the JSON output."""
    print("-> [Node: Validation Agent] Enforcing Pydantic data contract...")
    # Mocking a validation check
    if "blockers" not in state["report_draft"]:
        state["validation_errors"] = "Missing required field: 'blockers'"
    else:
        state["validation_errors"] = None
    return state

def correction_agent(state: AgentState):
    """Triggered if validation fails; passes the error message back to the LLM."""
    print(f"-> [Node: Correction Agent] Fixing errors: {state['validation_errors']}")
    state["retry_count"] += 1
    # Mocking the correction process
    state["report_draft"] = '{"sprint_id": "Sprint 12", "status": "At Risk", "blockers": "NTLM Timeouts Fixed"}'
    state["validation_errors"] = None
    return state

# ---------------------------------------------------------
# 3. DEFINE CONDITIONAL EDGES (The Router)
# ---------------------------------------------------------
def route_validation(state: AgentState):
    """Routes to END if validation succeeds, or Correction if it fails."""
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print("   [Router] Validation Failed! Routing to Correction Agent.")
        return "correction"
    else:
        print("   [Router] Validation Passed! Routing to END.")
        return "end"

# ---------------------------------------------------------
# 4. COMPILE THE STATE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

# Add our specialized nodes
workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

# Set the entry point
workflow.set_entry_point("drafting")

# Connect Drafting to Validation
workflow.add_edge("drafting", "validation")

# Add conditional routing from Validation
workflow.add_conditional_edges(
    "validation",
    route_validation,
    {
        "correction": "correction",
        "end": END
    }
)

# Connect Correction back to Validation for the loop
workflow.add_edge("correction", "validation")

# Compile the graph
agent_app = workflow.compile()

# ---------------------------------------------------------
# 5. EXECUTE THE WORKFLOW
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("INITIATING LANGGRAPH MULTI-AGENT NETWORK")
    print("=" * 50)
    
    initial_state = {
        "messages": ["Generate sprint status report"],
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0
    }
    
    final_state = agent_app.invoke(initial_state)
    print("\nFINAL STATE ACHIEVED:")
    print(final_state["report_draft"])