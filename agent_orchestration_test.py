import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from mock_local_llm import MockClient  # Importing our zero-egress simulator

# ---------------------------------------------------------
# 1. SETUP GRAPH STATE
# ---------------------------------------------------------
class AgentState(TypedDict):
    messages: List[str]
    report_draft: str
    validation_errors: str
    retry_count: int

# ---------------------------------------------------------
# 2. IMPLEMENT SPECIALIZED NODES
# ---------------------------------------------------------
def drafting_agent(state: AgentState):
    """Generates the structured project update report using the Mock LLM."""
    print("-> [Node: Drafting Agent] Synthesizing data into a report draft...")
    
    # Initialize our in-memory LLM simulator
    llm_client = MockClient()
    
    # Invoke the mock LLM
    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "\n".join(state["messages"])}]
    )
    
    # Extract the simulated JSON response
    state["report_draft"] = response.choices[0].message.content
    return state

def validation_agent(state: AgentState):
    """Checks if required fields are present in the JSON output."""
    print("-> [Node: Validation Agent] Enforcing Pydantic data contract...")
    
    # Load the LLM output as a dictionary to validate it
    try:
        draft_dict = json.loads(state["report_draft"])
        if "blockers" not in draft_dict:
            state["validation_errors"] = "Missing required field: 'blockers'"
        else:
            state["validation_errors"] = None
    except json.JSONDecodeError:
        state["validation_errors"] = "Output is not valid JSON."
        
    return state

def correction_agent(state: AgentState):
    """Triggered if validation fails; mocks the correction process."""
    print(f"-> [Node: Correction Agent] Fixing errors: {state['validation_errors']}")
    state["retry_count"] += 1
    
    # Simulating the LLM correcting its mistake
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
# 4. COMPILE AND EXECUTE THE STATE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

workflow.set_entry_point("drafting")
workflow.add_edge("drafting", "validation")

workflow.add_conditional_edges(
    "validation",
    route_validation,
    {
        "correction": "correction",
        "end": END
    }
)

workflow.add_edge("correction", "validation")
agent_app = workflow.compile()

if __name__ == "__main__":
    print("=" * 60)
    print("INITIATING STAGE 3: LANGGRAPH ORCHESTRATION TEST")
    print("=" * 60)
    
    initial_state = {
        "messages": ["Generate sprint status report using TFS and RAG data."],
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0
    }
    
    final_state = agent_app.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("FINAL STATE ACHIEVED:")
    print("=" * 60)
    # Pretty print the final JSON
    parsed_json = json.loads(final_state["report_draft"])
    print(json.dumps(parsed_json, indent=2))